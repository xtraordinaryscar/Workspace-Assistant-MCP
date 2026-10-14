"""
test_tools.py: call every tool function directly (no Claude needed).

Run from the mcp-server folder:   python test_tools.py

It creates a small set of sample files in a throwaway folder inside the system
temp directory, runs each tool, prints the results, and checks the safety layer.
The temp folder is deleted when the script ends, so nothing is left in the project.
"""

import atexit
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True   # don't leave a __pycache__ folder in the project

import server
from server import (
    analyze_text_file,
    generate_markdown_toc,
    generate_project_report,
    list_project_files,
    search_in_files,
    write_note,
)

# Point the server at a throwaway folder in the system temp directory.
# The tools read server.ROOT every time they run, so changing it here moves the
# whole sandbox (samples, notes/, saved reports) out of the project.
_temp_dir = tempfile.TemporaryDirectory(prefix="workspace_assistant_test_")
atexit.register(_temp_dir.cleanup)   # also runs if a test crashes
server.ROOT = Path(_temp_dir.name).resolve()
ROOT = server.ROOT

passed = 0
failed = 0


def check(name, condition):
    """Print PASS/FAIL for one check and keep the score."""
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")


def show(title, result):
    """Print a tool's output so you can read it yourself."""
    print(f"\n--- {title} ---")
    print(result)
    print()


# ---------------------------------------------------------------------------
# Create sample files
# ---------------------------------------------------------------------------

samples = ROOT / "test_samples"
samples.mkdir(exist_ok=True)

markdown_lines = [
    "# Workspace Assistant Demo",
    "",
    "This project uses Python and the Model Context Protocol (MCP) to give",
    "Claude helpful tools. Python makes the server easy to read and explain.",
    "",
    "## Installation",
    "",
    "Install the packages with pip.",
    "",
    "```",
    "# this is a code comment, not a heading",
    "```",
    "",
    "## Usage",
    "",
    "### Basic usage",
    "",
    "Ask Claude to analyze a file.",
    "",
    "## Usage",
    "",
    "A second section with the same title.",
]
(samples / "sample.md").write_text("\n".join(markdown_lines), encoding="utf-8")
(samples / "plain.txt").write_text(
    "Python is great.\nThe quick brown fox jumps over the lazy dog.\n", encoding="utf-8"
)
# Invalid UTF-8 bytes, to test the "not readable text" error
(samples / "broken.txt").write_bytes(b"\xff\xfe\x00\x80 not text")
# A file with an unsupported extension
(samples / "program.exe").write_bytes(b"MZ fake executable")

stamp = int(time.time())
note_name = f"test_note_{stamp}.md"
report_name = f"test_report_{stamp}.md"

# ---------------------------------------------------------------------------
# Normal behavior
# ---------------------------------------------------------------------------

print("=== list_project_files ===")
result = list_project_files("test_samples")
show("list_project_files('test_samples')", result)
check("lists sample.md", "sample.md" in result)
check("lists plain.txt", "plain.txt" in result)

result = list_project_files("test_samples", ".md")
check("extension filter keeps .md", "sample.md" in result and "plain.txt" not in result)
check("extension works without the dot", "sample.md" in list_project_files("test_samples", "md"))

print("\n=== analyze_text_file ===")
result = analyze_text_file("test_samples/sample.md")
show("analyze_text_file('test_samples/sample.md')", result)
check("reports word count", "Words:" in result)
check("finds 'python' keyword", "python" in result)
check("stop words are ignored", "    the:" not in result)

print("\n=== search_in_files ===")
result = search_in_files("python", "test_samples")
show("search_in_files('python', 'test_samples')", result)
check("finds a match in sample.md", "sample.md" in result)
check("search is case-insensitive", "plain.txt" in result)
check("no-match message", "No matches" in search_in_files("zzzzqqqq", "test_samples"))

print("\n=== generate_markdown_toc ===")
result = generate_markdown_toc("test_samples/sample.md")
show("generate_markdown_toc('test_samples/sample.md')", result)
check("has a heading link", "[Installation](#installation)" in result)
check("nested heading is indented", "  - [Basic usage](#basic-usage)" in result)
check("duplicate heading gets a suffix", "(#usage-1)" in result)
check("ignores '#' inside code blocks", "not a heading" not in result)

print("\n=== generate_project_report ===")
result = generate_project_report("test_samples")
show("generate_project_report('test_samples')", result)
check("report has a title", "# Project Report" in result)
check("report has a type table", "| Type | Files | Size |" in result)

result = generate_project_report("test_samples", report_name)
check("report can be saved", "Report saved to" in result)
check("saved report exists", (ROOT / "notes" / report_name).exists())
check(
    "saving again does not overwrite",
    "already exists" in generate_project_report("test_samples", report_name),
)

print("\n=== write_note ===")
result = write_note(note_name, "# Test note\n\nCreated by test_tools.py")
show("write_note", result)
check("note is created", "Note created" in result and (ROOT / "notes" / note_name).exists())
check("note is not overwritten", "already exists" in write_note(note_name, "new text"))

# ---------------------------------------------------------------------------
# Error handling and safety layer
# ---------------------------------------------------------------------------

print("\n=== errors and safety ===")
check("missing file gives an error", "Error: File not found" in analyze_text_file("nope.txt"))
check("folder instead of file", "Error" in analyze_text_file("test_samples"))
check("unsupported file type", "Unsupported file type" in analyze_text_file("test_samples/program.exe"))
check("invalid UTF-8 text", "not valid UTF-8" in analyze_text_file("test_samples/broken.txt"))
check("empty path", "Error" in analyze_text_file(""))
check("non-markdown file for TOC", "Error" in generate_markdown_toc("test_samples/plain.txt"))

check("blocks '..' (backslash)", "Access denied" in analyze_text_file("..\\hello.txt"))
check("blocks '..' (forward slash)", "Access denied" in analyze_text_file("../hello.txt"))
check("blocks absolute path", "Access denied" in analyze_text_file("C:\\Windows\\win.ini"))
check("blocks '..' in list", "Access denied" in list_project_files(".."))
check("blocks '..' in search", "Access denied" in search_in_files("x", ".."))
check("blocks '..' in report", "Access denied" in generate_project_report(".."))
check("note name cannot contain a path", "Invalid filename" in write_note("../evil.md", "x"))
check("note cannot use another extension", "Only these file types" in write_note("evil.exe", "x"))
check("note content cannot be empty", "empty" in write_note("empty.md", "   "))
check("report name cannot contain a path", "Invalid filename" in generate_project_report(".", "..\\r.md"))

# ---------------------------------------------------------------------------
# Delete the temp folder, then print the score
# ---------------------------------------------------------------------------

_temp_dir.cleanup()

print(f"\nResult: {passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)
