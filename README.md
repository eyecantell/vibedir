# VibeDir - Functionality is not yet ready, but "COMING SOON" #

VibeDir is a utility to facilitate code modifications when using an AI assistant. By integrating with `prepdir` and `applydir`, it generates prompts for large language models to modify a codebase. VibeDir supports manual workflows and in the future will support API integration with the latest GenAI models.

# Todo
- Build CLI menu selections and status items
- Build prompt - will create vibedir.txt when using API mode and vibedir_part1ofn.txt when using cut/paste mode. 
    [DEV_GUIDELINES]
    {dev.md}
    [/DEV_GUIDELINES]

    [CODEBASE]
    {prepdir output – filtered, UUID-scrubbed}
    [/CODEBASE]

    [CODE_CHANGE_INSTRUCTIONS]
    {applydir instruciotns}
    [/CODE_CHANGE_INSTRUCTIONS]

    [TASK]
    {User supplied task, note they can alternately type into the LLM window if using cut/paste mode}
    [/TASK]
- Git integration (commit each change so can be reverted, flatten on pr?) - configurable with GIT_COMMIT_EACH_CHANGE: true 
- Add status items to exmaple menu
- Add token counting (tiktoken) in order to keep treck of when to reshare dev.md, codebase for context (based on LLM context window)

---

## Overview  
`vibedir` enables **clipboard-driven UI** and **API-powered automation** for LLM development.  
- **UI**: Human-in-loop cut/paste to LLM UI (e.g. Grok, Claude, ChatGPT, other)
- **API**: Uses `apibump` (LiteLLM wrapper) for scripted calls and usage charges.
- **Shared**: `dev.md`, `prepdir`, token-aware safety

---

## Core Components

| Component | Role |
|---------|------|
| **`dev.md`** | Development guidelines, style, LLM behavior |
| **`prepdir`** | Clean, private, structured code output |
| **`applydir`** | Takes changes from LLM (in json) and applies them to the code base |
| **`vibedir`** | CLI based UI. UI orchestration, clipboard, token math |
| **`apibump`** | API client, model metadata, context limits |

---

## UI Flow (Clipboard / grok.com)

```text
1. User runs: vibedir prepare
   → prepdir cleans code
   → vibedir builds context
   → copies to clipboard
2. User pastes into LLM UI
3. vibedir warns if >70% limit