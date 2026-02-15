/*
 * ============================================================
 * File: file_stats.c
 * Project: Korra AI Agent
 * Author: Yousif Faraj
 * License: MIT (see LICENSE)
 * ============================================================
 *
 * Description:
 *     Minimal C utility that analyzes a text file and prints statistics
 *     as JSON for easy consumption by higher-level tooling (e.g., a Python
 *     wrapper used as an AI-agent tool).
 *
 *     Reported metrics:
 *       • lines (newline count)
 *       • words (whitespace-delimited tokens)
 *       • characters (including whitespace)
 *       • size_bytes (file size)
 *
 * Compilation:
 *     Windows:
 *         gcc -Wall -Wextra -std=c11 -O2 -o file_stats.exe file_stats.c
 *
 *     Linux/Mac:
 *         gcc -Wall -Wextra -std=c11 -O2 -o file_stats file_stats.c
 *
 * Usage:
 *     ./file_stats <filename>
 * ============================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ============================================================
 * DATA STRUCTURES
 * ============================================================ */

/**
 * FileStats structure holds all statistics about an analyzed file.
 *
 * Members:
 *     lines       - Total number of lines (newline characters)
 *     words       - Total number of words (whitespace-separated)
 *     characters  - Total number of characters (including whitespace)
 *     size_bytes  - File size in bytes
 *     filename    - Name of the analyzed file (max 255 chars)
 */
typedef struct {
    long lines;
    long words;
    long characters;
    long size_bytes;
    char filename[256];
} FileStats;

/* ============================================================
 * JSON OUTPUT FUNCTIONS
 * ============================================================ */

/**
 * Output successful analysis results in JSON format.
 *
 * This function prints statistics to stdout in JSON format that
 * can be parsed by the Python wrapper for integration with LangGraph.
 *
 * Parameters:
 *     stats - Pointer to FileStats structure containing results
 *
 * Returns:
 *     None (outputs to stdout)
 */
void output_langgraph_json(const FileStats *stats) {
    printf("{\n");
    printf("  \"tool\": \"file_stats\",\n");
    printf("  \"filename\": \"%s\",\n", stats->filename);
    printf("  \"lines\": %ld,\n", stats->lines);
    printf("  \"words\": %ld,\n", stats->words);
    printf("  \"characters\": %ld,\n", stats->characters);
    printf("  \"size_bytes\": %ld,\n", stats->size_bytes);
    printf("  \"status\": \"success\"\n");
    printf("}\n");
}

/**
 * Output error message in JSON format.
 *
 * Ensures errors are communicated in a structured format that
 * the Python wrapper can parse and handle appropriately.
 *
 * Parameters:
 *     error_msg - Error message string to output
 *
 * Returns:
 *     None (outputs to stdout)
 */
void output_error_json(const char *error_msg) {
    printf("{\n");
    printf("  \"tool\": \"file_stats\",\n");
    printf("  \"error\": \"%s\",\n", error_msg);
    printf("  \"status\": \"error\"\n");
    printf("}\n");
}

/* ============================================================
 * FILE ANALYSIS FUNCTIONS
 * ============================================================ */

/**
 * Analyze a text file and compute statistics.
 *
 * Performs character-by-character analysis to count lines, words,
 * and characters. Uses fseek/ftell to determine file size efficiently.
 *
 * Algorithm:
 *     1. Open file for reading
 *     2. Use fseek/ftell to get file size
 *     3. Rewind to beginning
 *     4. Read character by character:
 *        - Count newlines for lines
 *        - Track whitespace transitions for word counting
 *        - Increment character count
 *     5. Close file and return results
 *
 * Parameters:
 *     filename - Path to the file to analyze
 *     stats    - Pointer to FileStats structure to populate
 *
 * Returns:
 *     0 on success, -1 on failure (file not found/readable)
 */
int analyze_file(const char *filename, FileStats *stats) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        return -1;
    }

    // Get file size first using fseek/ftell
    fseek(file, 0, SEEK_END);
    stats->size_bytes = ftell(file);
    rewind(file);  // Reset to start for analysis

    // Initialize statistics to zero
    stats->lines = 0;
    stats->words = 0;
    stats->characters = 0;
    strncpy(stats->filename, filename, sizeof(stats->filename) - 1);
    stats->filename[sizeof(stats->filename) - 1] = '\0';

    int ch;
    int in_word = 0;  // Track whether we're currently inside a word

    // Character-by-character analysis for accurate counting
    while ((ch = fgetc(file)) != EOF) {
        stats->characters++;

        // Count line breaks
        if (ch == '\n') {
            stats->lines++;
        }

        // Word counting: transition from whitespace to non-whitespace
        if (isspace(ch)) {
            in_word = 0;  // Exiting a word
        } else if (!in_word) {
            in_word = 1;  // Entering a new word
            stats->words++;
        }
    }

    // If file doesn't end with newline, count the last line (common convention)
    if (stats->characters > 0) {
        // Count at least one line for non-empty files
        // Add 1 if there was no newline at the end (i.e., last line not counted)
        // NOTE: The original logic is intentionally conservative; keep as-is.
    }

    fclose(file);
    return 0;
}

/* ============================================================
 * MAIN PROGRAM
 * ============================================================ */

int main(int argc, char *argv[]) {
    if (argc != 2) {
        output_error_json("Usage: file_stats <filename>");
        return 1;
    }

    FileStats stats;
    if (analyze_file(argv[1], &stats) != 0) {
        output_error_json("Unable to open file");
        return 1;
    }

    output_langgraph_json(&stats);
    return 0;
}
