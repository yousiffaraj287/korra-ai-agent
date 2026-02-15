#!/usr/bin/env python3
"""
File: file_stats_tool.py
Project: Korra AI Agent
Author: Yousif Faraj

Description:
    LangGraph-compatible wrapper around a small C executable (`file_stats`)
    used for fast file-level analytics. This tool enables an agent to run
    system-level text inspection (lines / words / characters / size) and
    return structured JSON results to the model.

Highlights:
    • Cross-platform execution (Windows/Linux/Docker)
    • Subprocess-based integration with a compiled C binary
    • JSON output for reliable parsing and downstream reasoning
    • Defensive error handling (timeouts, decoding failures)

Requirements:
    - langchain-core
    - pathlib

Local build (example):
    Windows: gcc -o file_stats.exe file_stats.c
    Linux/Mac: gcc -o file_stats file_stats.c

Standalone test:
    python file_stats_tool.py <filename>
"""

# ============================================================
# IMPORTS
# ============================================================

import json
import subprocess
from pathlib import Path
import os
from langchain_core.tools import tool

# ============================================================
# TOOL DEFINITION
# ============================================================

@tool
def analyze_file_statistics(filename: str) -> dict:
    """
    Analyze text file statistics by invoking the compiled C tool.

    This function wraps a C-based file analysis program, enabling
    LangGraph agents to perform efficient file statistics operations.
    The C program analyzes the file and returns results as JSON, which
    this wrapper parses and returns to the agent.

    The tool counts:
        • Lines (newline characters)
        • Words (whitespace-separated tokens)
        • Characters (total including spaces)
        • File size (bytes)

    Args:
        filename: Path to the text file to analyze (relative or absolute)

    Returns:
        dict: Dictionary containing file statistics if successful:
              {
                  "tool": "file_stats",
                  "filename": "path/to/file.txt",
                  "lines": 42,
                  "words": 256,
                  "characters": 1843,
                  "size_bytes": 1890,
                  "status": "success"
              }

              Or error information if analysis fails:
              {
                  "error": "Error message",
                  "status": "error"
              }
    """
    try:
        # Locate the compiled executable (Windows uses .exe; Unix-like systems typically do not)
        binary = "file_stats.exe" if os.name == "nt" else "file_stats"
        tool_path = (Path(__file__).parent / binary).resolve()
        file_path = Path(filename).resolve()

        # Run the C tool via subprocess and capture output
        result = subprocess.run(
            [str(tool_path), str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Clean up stdout and stderr for parsing
        stdout_clean = result.stdout.strip()
        stderr_clean = result.stderr.strip()

        # Check if execution was successful
        if result.returncode == 0 and stdout_clean:
            try:
                # Escape backslashes for valid JSON (Windows path compatibility)
                stdout_clean = stdout_clean.replace("\\", "\\\\")
                return json.loads(stdout_clean)
            except json.JSONDecodeError as e:
                return {
                    "error": "Invalid JSON output from tool",
                    "raw_output": stdout_clean,
                    "status": "error",
                    "decode_error": str(e)
                }
        else:
            return {"error": f"Tool failed: {stderr_clean}", "status": "error"}

    except subprocess.TimeoutExpired:
        return {"error": "Tool execution timed out", "status": "error"}
    except Exception as e:
        return {"error": f"Integration error: {str(e)}", "status": "error"}

# ============================================================
# STANDALONE TEST PROGRAM
# ============================================================

if __name__ == "__main__":
    import sys

    # Validate command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python file_stats_tool.py <filename>")
        sys.exit(1)

    # Execute tool with provided filename
    result = analyze_file_statistics.invoke({"filename": sys.argv[1]})

    # Display formatted results
    print("LangGraph Tool Result:")
    print(json.dumps(result, indent=2))

    # Display tool metadata for verification
    print(f"\nTool Name: {analyze_file_statistics.name}")
    print(f"Tool Description: {analyze_file_statistics.description}")
    print(f"Tool Schema: {analyze_file_statistics.args}")

    print("\nReady to use with llm.bind_tools([analyze_file_statistics])")
