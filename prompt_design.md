# Vibedir Prompt Design

## Overview
This document captures the design decisions for the prompt management system in vibedir, a TUI-based tool for collaborating with LLMs on code generation. The core idea is a hybrid approach: the TUI provides a rendered chat view and quick input, while a backing Markdown file (`.vibedir/prompt.md`) serves as the source of truth, allowing users to edit prompts and history in their preferred editor/IDE.

Audience: Coders who prefer their own tools (e.g., Vim, VS Code) for editing, searching, and managing files.

Goals:
- Enable seamless bidirectional sync between TUI and file.
- Keep the file human-readable and git-friendly.
- Allow quick TUI interactions for simple additions.
- Support power-user workflows like forking sessions or scripting against history.

## File Format
The `.vibedir/prompt.md` file uses simple Markdown with strict, predictable section headers for easy parsing and readability. Headers are designed to be unique and unlikely to appear in normal content.

Example:
```markdown
# vibedir session — 2025-11-17T14:22:31

## User — 2025-11-17 14:22:31

Write a fastapi app that serves my plotly dashboards.

## Assistant (grok-4) — 2025-11-17 14:23:15

Here is the initial implementation...

```python
from fastapi import FastAPI
...
```

## User — 2025-11-17 14:25:10

Add authentication with JWT.

## Assistant (grok-4) — 2025-11-17 14:25:48

Updated with JWT auth...

## Pending → (edit below — Ctrl+Enter to send)

Make it use async and add rate limiting.
Also here is the current error I'm seeing:

```bash
Traceback (most recent call last):
  File ...
```
```

Rules:
- **Session Header**: Exactly one top-level `# vibedir session — <ISO-timestamp>` at the start (e.g., ISO 8601 without timezone for simplicity).
- **Message Sections**: 
  - `## User — YYYY-MM-DD HH:MM:SS` for user messages.
  - `## Assistant (<model>) — YYYY-MM-DD HH:MM:SS` for LLM responses (model in parens, e.g., `grok-4`).
- **Pending Section**: Always the last section: `## Pending → (edit below — Ctrl+Enter to send)`. This holds the in-progress prompt.
- **Formatting**: 
  - Blank line after every header.
  - Content under headers can include any Markdown (e.g., code blocks, lists, bold text).
  - No other lines start with `## ` to avoid parsing ambiguity.
- **Timestamps**: Use local time or UTC? Decide based on implementation (e.g., `datetime.now().strftime("%Y-%m-%d %H:%M:%S")`).
- **Parsing Regex**: Headers match `^## (User|Assistant \(.+?\)|Pending → .+) — \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` or similar. Content is everything until the next header.

This format ensures:
- Readability in any Markdown viewer or editor.
- Easy splitting/parsing (e.g., via regex or line-by-line scan).
- Delineation for TUI rendering (user left, assistant right, with dates/models as metadata).

## Sync Mechanism
- **Source of Truth**: The `.vibedir/prompt.md` file.
- **On App Start**:
  - If file exists: Load, parse, render history in TUI, set TextArea to Pending content.
  - If not: Create with session header + empty Pending section.
- **File Watcher** (using `watchdog` library):
  - Monitor `.vibedir/prompt.md` for external changes.
  - On change: Re-parse entire file, rebuild TUI chat history (add/remove bubbles), update TextArea with new Pending.
  - If Pending section is missing/malformed: Append a fresh empty one.
- **TUI Input (TextArea for Pending)**:
  - On keystroke (debounced 300-500ms): Rewrite *only* the Pending section in the file (preserve history).
  - If external change during debounce: Discard local changes, reload from file (external editor wins to avoid conflicts).
  - Ctrl+Enter (submit):
    - Append new `## User — <now>` with TextArea content.
    - Add empty `## Pending → ...` section.
    - Clear TextArea.
    - Send to LLM.
    - On LLM response: Append `## Assistant (<model>) — <now>` + response.
- **Conflict Handling**: Minimal risk since history is append-only and immutable; only Pending is editable. If user edits history externally, TUI reflects it immediately (useful for corrections).

## TUI Features
- **Display**: Rendered chat history in bubbles (user right-aligned, assistant left; Markdown support for code highlighting).
- **Input**: Multiline TextArea at bottom, synced to Pending section. Allows quick text additions without leaving TUI.
- **Layout Example**:
  ```
  ┌────────────────────────────────────────────────────────────┐
  │  Chat history (rendered bubbles, markdown, code highlighting) │
  │  (auto-scrolls, but can scroll up)                         │
  │                                                            │
  │  [🤖]  Here is the updated version with async...          │
  │                                                            │
  │  [👤]  Thanks, now add prometheus metrics                  │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
  ┌────────────────────────────────────────────────────────────┐
  │  ► Make it use SQLModel instead of plain SQLAlchemy       │
  │    Also here's my current models.py:                       │
  │                                                                    │
  │    (Ctrl+Enter to send  •  ⌘+Enter for newline  •  Esc to focus chat)  │
  └────────────────────────────────────────────────────────────┘
  ```
- **Performance**: For long histories, render only last N messages initially, with "Load earlier" button.
- **Commands**: CLI options like `vibedir continue path/to/prompt.md` to load specific files.

## Pain Points & Mitigations
- **Rapid Dual Editing**: Debounce TUI writes; let external changes override.
- **Malformed File**: Parser falls back gracefully (e.g., treat unknown sections as part of previous; recreate missing Pending).
- **Long Histories**: Lazy loading in TUI; file remains full for external tools.
- **Session Management**: Support loading old files; users can copy for branching.
- **Timestamp Conflicts**: Use seconds precision; if dupes, append milliseconds if needed.

## Bonus Features Enabled
- **Search/Grep**: Full history in file for IDE searching.
- **Git Integration**: Diff-friendly format for tracking changes.
- **Paste Large Content**: Drop code/errors into Pending via editor; TUI updates instantly.
- **Collaboration**: Multiple users editing same file (TUI + editor) works with watcher.
- **Retry/Edit History**: Delete/edit sections in editor; TUI syncs and allows resend.
- **Scripting**: Parse file for automation (e.g., extract code blocks).

## Open Questions / TODOs
- Timestamp format: Local vs UTC? Include timezone?
- Model Name: Hardcode or dynamic based on LLM used?
- Error Handling: What if file is locked/deleted mid-session?
- Multi-Project: Auto-detect `.vibedir/` in cwd, or require flag?
- Add your notes/changes here...

This design is ready for implementation. Start with file parser + writer, then watcher, then integrate into ChatWidget.