# Raw Sources

This directory contains your source documents. These are immutable — the LLM reads from them but never modifies them.

## Organization

You can organize sources however you like:
- By date: `2026-06/article-name.md`
- By topic: `psychology/`, `tech/`, `books/`
- Flat structure: All files in this directory

## Assets

Images and media files should go in `raw/assets/`.

## Obsidian Web Clipper

If using Obsidian Web Clipper:
1. Set it to save files to this `raw/` directory
2. Configure Settings → Files and links → "Attachment folder path" to `raw/assets/`
3. Use the "Download attachments" hotkey after clipping articles

## Adding Sources

To add a source:
1. Place the file in this directory
2. Tell the LLM to ingest it: "Please ingest {filename}"
3. The LLM will read it, create wiki pages, and update the index

## Format

Sources can be:
- Markdown files (`.md`)
- PDFs (`.pdf`)
- Text files (`.txt`)
- Images (`.jpg`, `.png`, etc.)
- Any format the LLM can read
