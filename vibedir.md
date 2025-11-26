# VibeDir - Functionality is not yet ready, but "COMING SOON" #
VibeDir is a utility to facilitate code modifications when using an AI assistant. It generates prompts for large language models to modify a codebase. VibeDir supports manual workflows (clipboard mode) and will soon support API integration with the latest GenAI models.

## Overview  
`vibedir` enables **clipboard-driven UI** and **API-powered automation** for LLM development.
- Two modes of operation:  
  - **Clipboard**: Human-in-loop cut/paste to LLM UI (e.g. Grok, Claude, ChatGPT, other)
  - **API**: Uses `apibump` (LiteLLM wrapper) for scripted calls and usage charges.


## WorkFlow

### User runs: vibedir CLI from the desired working directory
1. TUI menu pops up with options to:
  - Start new/Refresh session - this loads full session context (dev.md, code change instructions, etc.). Starting a new session backs up the existing prompt.md to prompt.md.{YYYY-MM-DD_HH-MM-SS} and creates a fresh prompt.md file. If not chosen the in-process session continues.
  - Define prompt (task, files, command results) for LLM (can be done in prompt.md)
  - Generate prompt (vibedir.txt file split into parts as needed if clipboard mode) that hold task and context information and copy to clipboard or send via API

  - On LLM answer
    - LLM UI answers with applydir.json format. 
    - For clipboard mode: User saves applydir.json to working directory
    - The applydir.json is automatically applied to the codebase (vibedir watching for file)
    - If auto_commit is configured then commit command is run (with the LLM generated or a generic commit message)
    - Any commands configured to run automatically are run async and (if configured) and results readied for next prompt

## TUI (in design phase, needs adjustment to Textual best practices)

### Main Menu v2 (three column layout) 'm' for menus list
Latest changes | Prompt | Command Results

All file names use FileLink class for easy opening

#### Latest changes column (left) 'd' diff, 'ctrl-r' revert
Errors: {errors list if errors exist from applying changes}

Latest changes by {model} (n files):
- file1.py [{number of changes in file1}]
- file2.py [{number of changes in file2}]
- ...

Other changes detected: # these are files that have been changed by user/other since last prompt send and will be automatically added to the prompt (middle column) but can be removed by the user by toggling here or in the middle (prompt) column.
{✓ if set to be in prompt| ☐ if not set to be in prompt}
- ✓ file3.md by {username}
- ☐ file4.py by {username}
- ...
- Previous commit message: {80 char preview of most recent commit message}
- Current commit message: {80 char preview of commit message to be used next}

Any files with auto-detected changes will be automatically included in the prompt column (user can remove them if desired).

Revert most recent changes requires revert_changes_command and changes_exist_command to be configured and is only available if changes have been made since last commit (changes_exist_result). This will also automatically add the reverted files to the prompt (and the user can remove them)

#### Prompt task column (center) (sync with prompt.md, see prompt_design.md), 'a' add file, If in api mode: 'ctrl-enter' to [commit current changes and] send, if clipboard mode: 'c' to [commit current changes and] copy prompt to clipboard
The [commit current changes and] portion of the Current Prompt top message will be displayed if changes have been made (as detected by changes_exist_result) and AUTO_COMMIT is set to 'previous'. This label/message updates reactively based on the mode, config, and state.

{Chat bubbles showing prompt history and latest prompt in progress, with support for Markdown rendering. Bubbles are aligned left for LLM/Assistant responses and right for User messages. The number of messages rendered is configurable (prompt_history_message_count with default 10), but the full history is maintained in prompt.md. Previous chat bubbles along with their associated file/results data scroll together.}

{Scrollable attachments (filenames and command names for command results) to be included in the prompt. This list is populated/unpopulated dynamically: by user selecting items from the right column (toggles sync bi-directionally), or by adding a file using 'a' (pops up a dialog for full path selection with textual picker) or by the auto-detect for changes made (in left column). Items can be removed by selecting an 'X' next to the file/results name. If a user removes a command result here, it is reflected in the right or left column (untoggles it).}

{Prompt task for quick entry/edit in a fixed text area at the bottom (below the attachments list), which remains accessible even when the chat history is scrolled.}

If there is a parse error in prompt.md, notify the user and provide options to retry (parse again after manual fix) or rebuild (rebuild from history dir).

The model name for assistant responses is supplied from the LLM response (e.g., in applydir.json). Timestamps use local time (e.g., datetime.now() without timezone).

#### Command results column (right), run manual command ('R') and include output in prompt ('r')

The status icons next to each of command will be configurable and have defaults:
- ✅ (success) if the configured command has run (since the last prompt sent) and it's success value yields true
- ❌ (failed) if the configured command has run (since the last prompt sent) and it's success value yields false
- {spinner} if the configured command is still running
- ❓ (not run) if the configured run_on value is empty and the configured command has not been run manually
- ⚠️ (not conifgured) if the command value is bad or not set in the configuration
- ⏳ (waiting) if the command is waiting for its configured run_on event to happen (since the last prompt send) before running
- {spinner} (running) if the command is currently running

{commands with their results in order of configuration}

{✓ if set to be in prompt| ☐ if not set to be in prompt} {command name} {status_icon}
- For Example:
  - ✓ Tests ✅
  - ✓ Lint ❌
  - ☐ Format ✅
  - ✓ Manual [{number of manual command results included in prompt}]

Toggling inclusion of command results here is reflected in the prompt column's inclusions list.

### Menus list: ('m') to return to main menu. 
1. Source Control settings
2. {Command 1 name} config
3. {Command 2 name} config
4. ...
5. {Command n name} config

### CLI Commands Menu Header (there will be one menu for each of the configured commands)
- Command Name: {name}
- Command: {command}
- Result: [success✅|running⏳|failed❌|not run❓] # uses configured icons plus wording
- Result in current prompt: [✓ Yes|☐ No]
- Run: {run_on}
- Success determined by: {success_value}
- Auto-Include results in prompt: {include_results}
- Result File: /my/test/results/file/full/path.txt # To be 'n/a' if not available - clickable (FileLink) for vscode edit

### CLI Commands Menu
1. Run {name} ({command})
2. [Add results to prompt|Remove results from prompt] # depending on current prompt state
3. Configure this command (can also edit .vibedir/config.toml directly) # If selected this will open a walkthrough of each command setting

### CLI UI Source Control Menu Header
- TBD
### CLI UI Source Control Menu 
- TBD
---

## vibedir.txt
The vibedir.txt file is generated from the codebase, dev.md, and other auxillary information needed in order to give na LLM all of the information needed to begin working with the developer. It is used on session init and refresh (for context window) in the cut/paste mode, and every time in API mode. Empty tags are not included.

The format will be similar to the following:
```
    [DEV_GUIDELINES]
    {dev.md contents}
    [/DEV_GUIDELINES]

    [CODEBASE]
    {prepdir output – filtered, UUID-scrubbed}
    [/CODEBASE]

    [CODE_CHANGE_INSTRUCTIONS]
    {applydir instructions including json format}
    [/CODE_CHANGE_INSTRUCTIONS]

    [COMMANDS_AND_RESULTS]
    {commands and results if they have been run and are set to be shared}
    [/<COMMANDS_AND_RESULTS]

    [TASK]
    {User supplied task, note they can alternately type into the LLM window if using cut/paste mode}
    [/TASK]
  ```

The DEV_GUIDELINES, CODEBASE, and CODE_CHANGE_INSTRUCTIONS will be included on session start or refresh. 

The COMMANDS_AND_RESULTS will contain each command (plus its results) if it is set to be included in the prompt and has been run 

The TASK will be supplied if a task has been defined by the user (there may be times that the command results just speak for themselves)

#### Splitting vibedir.txt into vibedir_part1ofn.txt parts
If the user is in clipboard mode, then the vibedir.txt will be split into (clipboard_max_chars_per_file char) parts named vibedir_part1ofn.text in order to avoid truncation by the LLM UI. 

## Core Components

| Component | Role |
|---------|------|
| **`dev.md`** | Development guidelines, style, LLM behavior |
| **`prepdir`** | Clean, private, structured code output |
| **`applydir`** | Takes changes from LLM (in json described in CODE_CHANGE_INSTRUCTIONS) and applies them to the code base |
| **`fileclip`** | Clipboard control (for pasting files into UI) |
| **`vibedir`** | CLI based UI. UI orchestration, clipboard, token math |
| **`apibump`** | API client (includes LiteLLM wrapper), model metadata, context limits, analytics |

---

### Token Counting
- In CLIPBOARD mode, request tokens are counted for each generated prompt, and once 70% of the LLM context window has been reached, an automatic refresh will be triggered (where dev.md, code, and guidelines are reshared). We can also count tokens received in teh applydir.json file, but we have no way to count additional prompt information added by the user in the LLM UI, or additional response information outside of the applydir.json file.  
- In API mode, all prompt/response tokens are counted. 

## Todo
- Build CLI menu selections and status items (test config, latest number of changes, latest commit message, latest token count)
- Build prompt - will create vibedir.txt when using API mode and vibedir_part1ofn.txt when using cut/paste mode. 
- Git integration (commit each change so can be reverted, flatten on pr?) - configurable (see config)
- Tests configuration
- Add token counting (tiktoken) in order to keep track of when to reshare dev.md, codebase for context (based on LLM context window)