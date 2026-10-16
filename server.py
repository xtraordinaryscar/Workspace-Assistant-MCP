"""
workspace-assistant: a small MCP server that gives Claude safe, useful tools
for working with a project folder.

Safety rules (enforced by safe_path below):
  * Every path is resolved relative to THIS folder (mcp-server).
  * Anything that ends up outside this folder is rejected (.., absolute paths, etc.).
  * Writing is limited. save_new_file() creates NEW .md/.txt files in notes/
    (used by write_note and by generate_project_report with save_as). str_replace
    edits existing text files, but never server.py. delete_file moves a file into
    .trash/ (recoverable), never erases it, and never touches server.py.
  * git_lite runs only three fixed, read-only git commands (status, log, diff).

Tools: list_project_files, analyze_text_file, search_in_files,
generate_markdown_toc, generate_project_report, write_note, find_todos,
find_broken_links, read_file, str_replace, delete_file, git_lite.

Run it with:  python server.py
It serves MCP over streamable HTTP on 127.0.0.1 (port from the PORT environment
variable, default 8000). It has no login; it is meant to be exposed only through
a temporary tunnel (for example Cloudflare Quick Tunnel) during a demo.
"""

import math
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import uvicorn
from mcp.server.fastmcp import FastMCP

# The server object. The name is what Claude shows in its tools list.
mcp = FastMCP("workspace-assistant")

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# The allowed folder = the folder this file lives in (the mcp-server folder).
ROOT = Path(__file__).parent.resolve()

NOTES_DIR = "notes"             # the only place new files may be created
MAX_READ_BYTES = 1_000_000      # skip/refuse files bigger than ~1 MB
MAX_WRITE_CHARS = 100_000       # largest note we will create
MAX_LIST = 200                  # most files shown in a listing
MAX_MATCHES = 50                # most search matches returned
WORDS_PER_MINUTE = 200          # average reading speed

# Only these file types are treated as readable text.
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".csv", ".log",
    ".html", ".css", ".js", ".yaml", ".yml", ".toml", ".ini",
}

# Folders we never look inside.
IGNORED_FOLDERS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}

# Common English words ignored when counting keywords.
STOP_WORDS = set(
    """a about above after again all also am an and any are as at be because been
    before being below between both but by can could did do does doing down during
    each few for from further had has have having he her here hers him his how i if
    in into is it its just me more most my no nor not of off on once only or other
    our out over own same she should so some such than that the their them then
    there these they this those through to too under until up us very was we were
    what when where which while who why will with would you your""".split()
)


class UserError(Exception):
    """An expected problem (bad path, wrong file type...). The message is shown to Claude."""


# ---------------------------------------------------------------------------
# Safety layer and small helpers
# ---------------------------------------------------------------------------

def safe_path(user_path: str) -> Path:
    """Turn a user-supplied path into a real path, guaranteed to be inside ROOT.

    Works because resolve() removes '..' and follows symlinks BEFORE we check
    where the path ended up. Absolute paths like C:\\Windows are caught too,
    since they resolve to somewhere outside ROOT.
    """
    if user_path is None or not str(user_path).strip():
        raise UserError("The path is empty.")

    candidate = (ROOT / str(user_path).strip()).resolve()

    try:
        candidate.relative_to(ROOT)  # raises ValueError if candidate is outside ROOT
    except ValueError:
        raise UserError(
            "Access denied: that path is outside the allowed folder (mcp-server)."
        )
    return candidate


def safe_folder(subfolder: str) -> Path:
    """Like safe_path, but the result must be an existing folder."""
    folder = safe_path(subfolder)
    if not folder.exists():
        raise UserError(f"Folder not found: {subfolder}")
    if not folder.is_dir():
        raise UserError(f"That is a file, not a folder: {subfolder}")
    return folder


def rel(path: Path) -> str:
    """Show a path relative to ROOT (shorter and avoids leaking the full path)."""
    return str(path.relative_to(ROOT))


def fmt_size(num_bytes: int) -> str:
    """Make a byte count human-readable, e.g. 2048 -> '2.0 KB'."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def read_text_file(user_path: str):
    """Safely read a small UTF-8 text file. Returns (resolved_path, text)."""
    path = safe_path(user_path)
    if not path.exists():
        raise UserError(f"File not found: {user_path}")
    if not path.is_file():
        raise UserError(f"That is a folder, not a file: {user_path}")
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        raise UserError(
            f"Unsupported file type '{path.suffix}'. Supported: "
            + ", ".join(sorted(TEXT_EXTENSIONS))
        )
    if path.stat().st_size > MAX_READ_BYTES:
        raise UserError(f"File is too large (limit is {fmt_size(MAX_READ_BYTES)}).")
    try:
        # utf-8-sig also handles the invisible BOM that Windows Notepad adds
        return path, path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise UserError("This file is not valid UTF-8 text, so it can't be read.")


def collect_files(folder: Path) -> list:
    """List every file under `folder`, skipping ignored folders and anything
    that (through a symlink) points outside ROOT."""
    found = []
    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_FOLDERS for part in p.relative_to(ROOT).parts):
            continue
        try:
            p.resolve().relative_to(ROOT)
        except ValueError:
            continue
        found.append(p)
    return sorted(found)


def save_new_file(filename: str, content: str, allowed_extensions: set) -> Path:
    """The ONLY function that writes to disk.

    It can only create a brand-new file with a plain name inside notes/.
    It cannot overwrite, and it cannot write anywhere else.
    """
    filename = filename.strip()
    if not re.fullmatch(r"[A-Za-z0-9_\- ]+\.[A-Za-z0-9]+", filename):
        raise UserError(
            "Invalid filename. Use only letters, numbers, spaces, '-' or '_', "
            "followed by an extension (no folders or slashes)."
        )
    if Path(filename).suffix.lower() not in allowed_extensions:
        raise UserError(
            "Only these file types can be created: " + ", ".join(sorted(allowed_extensions))
        )
    if not content.strip():
        raise UserError("The content is empty.")
    if len(content) > MAX_WRITE_CHARS:
        raise UserError(f"Content is too long (limit is {MAX_WRITE_CHARS} characters).")

    target = safe_path(f"{NOTES_DIR}/{filename}")   # still goes through the safety check
    target.parent.mkdir(exist_ok=True)
    try:
        # mode "x" = create only; fails if the file already exists (no overwriting)
        with open(target, "x", encoding="utf-8") as f:
            f.write(content)
    except FileExistsError:
        raise UserError(
            f"'{filename}' already exists in {NOTES_DIR}/. "
            "Existing files are never overwritten, so please choose a different name."
        )
    return target


# ---------------------------------------------------------------------------
# Tool 1: list files (read-only)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_project_files(subfolder: str = ".", extension: str = "") -> str:
    """List the files in the project folder with their size and last-modified date.

    Args:
        subfolder: Folder to look in, relative to the project root. Default is the root.
        extension: Optional filter such as ".md" or "txt".
    """
    try:
        folder = safe_folder(subfolder)
        files = collect_files(folder)

        if extension.strip():
            ext = extension.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            files = [p for p in files if p.suffix.lower() == ext]

        if not files:
            return "No matching files found."

        lines = [f"Found {len(files)} file(s) in '{rel(folder)}':"]
        for p in files[:MAX_LIST]:
            info = p.stat()
            modified = datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"- {rel(p)} | {fmt_size(info.st_size)} | modified {modified}")
        if len(files) > MAX_LIST:
            lines.append(f"... and {len(files) - MAX_LIST} more (showing the first {MAX_LIST}).")
        return "\n".join(lines)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 2: analyze a text file (read-only, content analysis)
# ---------------------------------------------------------------------------

@mcp.tool()
def analyze_text_file(path: str) -> str:
    """Analyze a text file: word count, line count, reading time and top keywords.

    Args:
        path: Path to a text file (.txt, .md, .py, ...), relative to the project root.
    """
    try:
        file_path, text = read_text_file(path)

        word_count = len(text.split())
        line_count = len(text.splitlines())
        reading_minutes = max(1, math.ceil(word_count / WORDS_PER_MINUTE)) if word_count else 0

        # Count keywords: lowercase words, at least 3 letters, not common stop words
        keywords = Counter()
        for word in re.findall(r"[a-z']+", text.lower()):
            word = word.strip("'")
            if len(word) >= 3 and word not in STOP_WORDS:
                keywords[word] += 1

        lines = [
            f"Analysis of {rel(file_path)}",
            f"- Words: {word_count}",
            f"- Lines: {line_count}",
            f"- Characters: {len(text)}",
            f"- Estimated reading time: about {reading_minutes} min (at {WORDS_PER_MINUTE} words/min)",
            "- Top keywords:",
        ]
        if keywords:
            for word, count in keywords.most_common(10):
                lines.append(f"    {word}: {count}")
        else:
            lines.append("    (none found)")
        return "\n".join(lines)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 3: search inside files (read-only)
# ---------------------------------------------------------------------------

@mcp.tool()
def search_in_files(keyword: str, subfolder: str = ".") -> str:
    """Search all text files for a keyword (case-insensitive) and show matching lines.

    Args:
        keyword: The word or phrase to look for.
        subfolder: Folder to search in, relative to the project root. Default is the root.
    """
    try:
        if not keyword or not keyword.strip():
            return "Error: the keyword is empty."

        folder = safe_folder(subfolder)
        needle = keyword.strip().lower()
        matches = []
        files_searched = 0

        for p in collect_files(folder):
            if p.suffix.lower() not in TEXT_EXTENSIONS or p.stat().st_size > MAX_READ_BYTES:
                continue
            try:
                text = p.read_text(encoding="utf-8-sig")
            except (UnicodeDecodeError, OSError):
                continue  # skip files we can't read
            files_searched += 1
            for number, line in enumerate(text.splitlines(), start=1):
                if needle in line.lower():
                    matches.append(f"{rel(p)}:{number}: {line.strip()[:150]}")

        if not matches:
            return f"No matches for '{keyword}' (searched {files_searched} text file(s))."

        lines = [f"Found {len(matches)} match(es) for '{keyword}' in {files_searched} file(s):"]
        lines.extend(matches[:MAX_MATCHES])
        if len(matches) > MAX_MATCHES:
            lines.append(f"... and {len(matches) - MAX_MATCHES} more (showing the first {MAX_MATCHES}).")
        return "\n".join(lines)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 4: Markdown table of contents (read-only, generates text)
# ---------------------------------------------------------------------------

def make_anchor(title: str) -> str:
    """Build a GitHub-style link anchor: 'My Title!' -> 'my-title'."""
    anchor = title.lower().strip()
    anchor = re.sub(r"[^\w\s-]", "", anchor)   # drop punctuation
    return re.sub(r"\s", "-", anchor)          # spaces -> hyphens


@mcp.tool()
def generate_markdown_toc(path: str) -> str:
    """Generate a Markdown table of contents from the headings of a .md file.
    The file itself is NOT modified; the TOC is just returned.

    Args:
        path: Path to a Markdown (.md) file, relative to the project root.
    """
    try:
        file_path, text = read_text_file(path)
        if file_path.suffix.lower() != ".md":
            return "Error: this tool only works on Markdown (.md) files."

        headings = []          # list of (level, title)
        in_code_block = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block   # '#' inside code is not a heading
                continue
            if in_code_block:
                continue
            match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if match:
                headings.append((len(match.group(1)), match.group(2)))

        if not headings:
            return f"No headings found in {rel(file_path)}."

        top_level = min(level for level, _ in headings)
        seen = {}              # handles repeated headings (usage, usage-1, ...)
        toc = ["## Table of Contents", ""]
        for level, title in headings:
            anchor = make_anchor(title)
            if anchor in seen:
                seen[anchor] += 1
                anchor = f"{anchor}-{seen[anchor]}"
            else:
                seen[anchor] = 0
            indent = "  " * (level - top_level)
            toc.append(f"{indent}- [{title}](#{anchor})")
        return "\n".join(toc)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 5: project report (generates text; optionally saves it)
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_project_report(subfolder: str = ".", save_as: str = "") -> str:
    """Generate a Markdown summary report of a folder: file counts by type,
    total size, largest files and most recently changed files.

    Args:
        subfolder: Folder to summarize, relative to the project root. Default is the root.
        save_as: Optional filename (e.g. "report.md"). If given, the report is also saved
                 as a NEW file inside the notes/ folder. Existing files are never overwritten.
    """
    try:
        folder = safe_folder(subfolder)
        files = collect_files(folder)
        if not files:
            return "The folder has no files to report on."

        sizes = {p: p.stat().st_size for p in files}
        total_size = sum(sizes.values())

        # Group by file type
        count_by_type = Counter()
        size_by_type = Counter()
        for p in files:
            kind = p.suffix.lower() or "(no extension)"
            count_by_type[kind] += 1
            size_by_type[kind] += sizes[p]

        largest = sorted(files, key=lambda p: sizes[p], reverse=True)[:5]
        newest = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]

        lines = [
            "# Project Report",
            "",
            f"- Folder: `{rel(folder)}`",
            f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"- Total files: {len(files)}",
            f"- Total size: {fmt_size(total_size)}",
            "",
            "## Files by type",
            "",
            "| Type | Files | Size |",
            "|---|---|---|",
        ]
        for kind, count in count_by_type.most_common():
            lines.append(f"| {kind} | {count} | {fmt_size(size_by_type[kind])} |")

        lines += ["", "## Largest files", ""]
        for p in largest:
            lines.append(f"- {rel(p)} ({fmt_size(sizes[p])})")

        lines += ["", "## Recently modified", ""]
        for p in newest:
            modified = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"- {rel(p)} ({modified})")

        report = "\n".join(lines)

        if save_as.strip():
            saved = save_new_file(save_as, report, {".md"})
            report += f"\n\n_Report saved to {rel(saved)}_"
        return report
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 6: write a note (the only tool that writes, and only new files in notes/)
# ---------------------------------------------------------------------------

@mcp.tool()
def write_note(filename: str, content: str) -> str:
    """Create a NEW note file (.md or .txt) inside the notes/ folder.
    It never overwrites an existing file and cannot write anywhere else.

    Args:
        filename: Plain file name such as "ideas.md" (no folders or slashes).
        content: The text to put in the note.
    """
    try:
        saved = save_new_file(filename, content, {".md", ".txt"})
        return f"Note created: {rel(saved)} ({len(content)} characters)."
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 7: find TODO / FIXME / NOTE markers (read-only)
# ---------------------------------------------------------------------------

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|NOTE)\b[:\s-]*(.*)")   # uppercase markers only


@mcp.tool()
def find_todos(subfolder: str = ".") -> str:
    """Find TODO, FIXME and NOTE markers (uppercase) in text files and list where they are.

    Args:
        subfolder: Folder to scan, relative to the project root. Default is the root.
    """
    try:
        folder = safe_folder(subfolder)
        found = []
        files_scanned = 0

        for p in collect_files(folder):
            if p.suffix.lower() not in TEXT_EXTENSIONS or p.stat().st_size > MAX_READ_BYTES:
                continue
            try:
                text = p.read_text(encoding="utf-8-sig")
            except (UnicodeDecodeError, OSError):
                continue  # skip files we can't read
            files_scanned += 1
            for number, line in enumerate(text.splitlines(), start=1):
                match = TODO_PATTERN.search(line)
                if match:
                    found.append(f"{rel(p)}:{number}: [{match.group(1)}] {match.group(2).strip()[:100]}")

        if not found:
            return f"No TODO, FIXME or NOTE markers found (scanned {files_scanned} text file(s))."

        lines = [f"Found {len(found)} marker(s) (scanned {files_scanned} text file(s)):"]
        lines.extend(found[:MAX_MATCHES])
        if len(found) > MAX_MATCHES:
            lines.append(f"... and {len(found) - MAX_MATCHES} more (showing the first {MAX_MATCHES}).")
        return "\n".join(lines)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 8: find broken relative links in a Markdown file (read-only)
# ---------------------------------------------------------------------------

LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)[^)]*\)")   # [text](target "optional title")


@mcp.tool()
def find_broken_links(path: str) -> str:
    """Check the relative links in a Markdown file and report any that point to
    files or folders that don't exist. External links (http, mailto) and #anchors
    are skipped, and anchors inside other files are not checked.

    Args:
        path: Path to a Markdown (.md) file, relative to the project root.
    """
    try:
        file_path, text = read_text_file(path)
        if file_path.suffix.lower() != ".md":
            return "Error: this tool only works on Markdown (.md) files."

        checked = 0
        broken = []
        in_code_block = False
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block   # links inside code blocks are examples
                continue
            if in_code_block:
                continue
            for target in LINK_PATTERN.findall(line):
                # Skip #anchors and external links such as http:, https:, mailto:
                if target.startswith("#") or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]+:", target):
                    continue
                link_path = unquote(target.split("#")[0].split("?")[0])
                if not link_path:
                    continue
                checked += 1
                try:
                    full_path = safe_path(f"{rel(file_path.parent)}/{link_path}")
                except UserError:
                    broken.append(f"line {number}: {target} -> outside the allowed folder (not checked)")
                    continue
                if not full_path.exists():
                    broken.append(f"line {number}: {target} -> not found")

        if checked == 0:
            return f"No relative links found in {rel(file_path)}."
        if not broken:
            return f"Checked {checked} relative link(s) in {rel(file_path)}: none are broken."
        lines = [f"Checked {checked} relative link(s) in {rel(file_path)}: {len(broken)} broken."]
        lines.extend(broken)
        return "\n".join(lines)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 9: read a file with line numbers (read-only)
# ---------------------------------------------------------------------------

# The server's own code file. str_replace and delete_file refuse to touch it.
PROTECTED_FILE = Path(__file__).resolve()


def is_protected(file_path: Path) -> bool:
    """True if this path is the server's own code file."""
    return file_path.resolve() == PROTECTED_FILE


@mcp.tool()
def read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """Read a text file and return its lines with line numbers, so you can see the
    exact code. Long files come back in parts: call again with start_line to continue.

    Args:
        path: Path to a text file, relative to the project root.
        start_line: First line to return (1 is the top of the file).
        max_lines: Most lines to return in one call (default 200, maximum 500).
    """
    try:
        file_path, text = read_text_file(path)
        lines = text.splitlines()
        total = len(lines)
        if total == 0:
            return f"{rel(file_path)} is empty."
        if start_line < 1 or start_line > total:
            return f"Error: start_line must be between 1 and {total} for this file."

        max_lines = max(1, min(max_lines, 500))
        end = min(total, start_line + max_lines - 1)
        width = len(str(end))

        out = [f"{rel(file_path)} (lines {start_line}-{end} of {total}):"]
        for number in range(start_line, end + 1):
            out.append(f"{number:>{width}} | {lines[number - 1]}")
        if end < total:
            out.append(f"... more lines remain. Call read_file again with start_line={end + 1}.")
        return "\n".join(out)
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 10: replace one exact piece of text in an existing file
# ---------------------------------------------------------------------------

@mcp.tool()
def str_replace(path: str, old_str: str, new_str: str) -> str:
    """Replace one exact piece of text in an existing text file. The old text must
    appear exactly once, otherwise nothing is changed. It cannot create or delete
    files, and it cannot edit the server's own code file.

    Args:
        path: Path to an existing text file, relative to the project root.
        old_str: The exact text to find (copy it from read_file, including spaces).
        new_str: The text to put in its place (can be empty to remove old_str).
    """
    try:
        if not old_str:
            return "Error: old_str is empty. Give the exact text to replace."
        if is_protected(safe_path(path)):
            return "Error: this file is protected and cannot be edited through this tool."

        file_path, text = read_text_file(path)
        count = text.count(old_str)
        if count == 0:
            return f"Error: old_str was not found in {rel(file_path)}. Nothing was changed."
        if count > 1:
            return (f"Error: old_str appears {count} times in {rel(file_path)}. "
                    "Add more surrounding text so it matches exactly once. Nothing was changed.")

        line_number = text[:text.index(old_str)].count("\n") + 1
        file_path.write_text(text.replace(old_str, new_str, 1), encoding="utf-8")
        return (f"Replaced 1 occurrence in {rel(file_path)} at line {line_number} "
                f"({len(old_str)} characters replaced with {len(new_str)}).")
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 11: delete a file safely (it is moved into .trash/, never erased)
# ---------------------------------------------------------------------------

TRASH_DIR = ".trash"


@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file by moving it into the .trash/ folder, so it can be recovered.
    Nothing is permanently erased. Folders cannot be deleted, and the server's own
    code file is protected.

    Args:
        path: Path to a file, relative to the project root.
    """
    try:
        file_path = safe_path(path)
        if is_protected(file_path):
            return "Error: this file is protected and cannot be deleted through this tool."
        if TRASH_DIR in file_path.relative_to(ROOT).parts:
            return "Error: this file is already in .trash and cannot be deleted again."
        if not file_path.exists():
            return f"Error: file not found: {path}"
        if not file_path.is_file():
            return "Error: only files can be deleted, not folders."

        trash = ROOT / TRASH_DIR
        trash.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        destination = trash / f"{stamp}_{file_path.name}"
        original = rel(file_path)
        file_path.rename(destination)
        return (f"Moved {original} to {rel(destination)}. "
                "It is recoverable: move it back to restore it.")
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Tool 12: read-only git information (git-lite)
# ---------------------------------------------------------------------------

# Only these fixed, read-only git commands can run. No shell is used, and the
# command name is looked up in this table, so nothing else can be executed.
GIT_COMMANDS = {
    "status": ["git", "status", "--short"],
    "log": ["git", "log", "--oneline", "-n", "10"],
    "diff": ["git", "diff", "--stat"],
}


@mcp.tool()
def git_lite(command: str = "status") -> str:
    """Show read-only git information for the project: 'status' (changed files),
    'log' (last 10 commits) or 'diff' (summary of uncommitted changes).
    Nothing is ever changed.

    Args:
        command: One of "status", "log" or "diff". Default is "status".
    """
    try:
        key = command.strip().lower()
        if key not in GIT_COMMANDS:
            return "Error: command must be one of: " + ", ".join(GIT_COMMANDS) + "."
        result = subprocess.run(
            GIT_COMMANDS[key], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return f"Error from git: {result.stderr.strip() or 'unknown error'}"
        output = result.stdout.strip()
        if not output:
            return f"git {key}: nothing to show."
        return f"git {key}:\n{output}"
    except FileNotFoundError:
        return "Error: git is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return "Error: git took too long to respond."
    except (UserError, OSError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Start the server over streamable HTTP (no login; use only behind a temporary tunnel)
# ---------------------------------------------------------------------------

class HostFix:
    """Replaces the Host header on incoming HTTP requests with a localhost value.

    Tunnels forward requests with their own hostname. The MCP SDK refuses
    hostnames that are not localhost, so we set the header to 127.0.0.1 first.
    The server still only listens on 127.0.0.1, so this does not open it up.
    """

    def __init__(self, app, local_host: str):
        self.app = app
        self.local_host = local_host.encode("ascii")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = [(k, v) for k, v in scope["headers"] if k != b"host"]
            headers.append((b"host", self.local_host))
            scope = {**scope, "headers": headers}
        await self.app(scope, receive, send)


def main():
    # 1. Port comes from the PORT environment variable (default 8000)
    port_text = os.environ.get("PORT", "8000").strip()
    try:
        port = int(port_text)
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        sys.exit(f"Refusing to start: PORT must be a number from 1 to 65535 (got '{port_text}').")

    # 2. Streamable HTTP app from the SDK. Bound to 127.0.0.1 only, so it is not
    #    reachable from the network; a tunnel forwards outside traffic to it.
    #    The MCP endpoint is served at the path /mcp.
    # The SDK rejects any Host header that is not localhost ("421 Invalid Host
    # header"), but tunnels send their own hostname. HostFix rewrites the header
    # to the local address before the SDK checks it.
    app = HostFix(mcp.streamable_http_app(), f"127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
