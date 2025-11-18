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
  - Start new session (or refresh session) - this loads full session context (dev.md, code change instructions, etc.)
  - Define prompt (task, files, command results) for LLM (can be done in prompt.md)
  - Generate prompt (vibedir.txt file split into parts as needed if clipboard mode) that hold task and context information and copy to clipboard or send via API

  - On LLM answer
    - LLM UI answers with applydir.json format. 
    - For clipboard mode: User saves applydir.json to working directory
    - The applydir.json is automatically applied to the codebase (vibedir watching for file)
    - If auto_commit is configured then commit command is run (with the LLM generated or a generic commit message)
    - Any commands configured to run automatically are run and (if configured) results readied for next prompt

## TUI (in design phase, needs adjustment to Textual best practices)

### Main Menu Header v1
- Current Prompt: Press 's|c' to [commit current changes and] [send|copy prompt to clipboard]
  - Errors: [Error(s) encountered when applying latest changes.]
  - Results: [Tests {status_icon} - [Lint {status_icon} - [{command name}{status_icon}
  - Auxillary: {comma delim list of up to 5 included files... n more} 
  - Task ('t' to [set|edit]): [preview of current task wording...] 

- Other Results: [Tests {status_icon} - [Lint {status_icon} - [{command name}{status_icon}
- Latest Changes: {status_icon}
- Status Legend: success ✅ - running {spinner} - failed ❌ -  not run ❓ - bad config ⚠️ - waiting ⏳
- LLM Changes: {comma delim list of up to 5 included files... n more} 
- External Changes: {comma delim list of up to 5 included files... n more} 

         
- Menus: ('m') Source Control settings, boilerplate for each configured [command]
- Previous commit: (Last commit message)
- Working commit: (Working commit message) # if current changes

### Notes on Main Menu Header v1 fields:
The [commit current changes and] portion of the Current Prompt top message will be displayed if changes have been made (as detected by changes_exist_result) and AUTO_COMMIT is set to 'previous'.

The [send|copy prompt to clipboard] will be "send" if mode = api, and "copy prompt to clipboard" if mode = clipboard

Errors line is only shown if errors have been encountered on the latest apply_code_changes (e.g. applydir) attempt.

Each of the command results (e.g. Test, Lint) will be shown in either the Results in Prompt section (if include_results=true) or the other Results section (if include_results=true). 

The status icons next to each of command will be:
- ✅ if the configured command has run and it's success value yields true
- ❌ if the configured command has run and it's success value yields false
- {spinner} if the configured command is still running
- ❓ if the configured run_on value is empty and the configured command has not been run manually
- ⚠️ if the command value is not set in the configuration
- ⏳ if the command is waiting for its configured run_on event to happen before running

### Main Menu v1
1. Edit task for prompt ('e')
2. Add files to prompt ('a')

3. Run tests ('t') # if TEST_COMMAND available
3. Re-run tests ('t') $ TEST_COMMAND available and test results available
4. Add Test Results to prompt # only if test results are available and not already in prompt

5. Run lint # if LINT_COMMAND available
5. Re-run lint # LINT_COMMAND available and lint results available
6. Add Linting Results # only if linting results are available and not already in prompt
5. Run CMD # if CMD_COMMAND available
5. Add CMD Results # only if AUTO_COMMAND results are available and not already in prompt
6. Run command ('R') and include output in prompt ('r')
7. Revert most recent changes [requires REVERT_CHANGES_COMMAND, CHANGES_EXIST_COMMAND, changes_exist_result] # only if changes have been made since last commit (changes_exist_result)

### Main Menu Header v2

Latest changes (n files) 'd' diff 'r' revert |  Prompt 'ctrl-enter' to send (sync with prompt.md, see prompt_design.md) | Command Results (in prompt/out of prompt)
file1.py                                     
file2.py
...

### CLI UI Test/Lint/CMD Menu Header
Test results in prompt: [Yes|No]
Result: [success✅|running⏳|failed❌|not run❓]
Result File: /my/temp/test/results/file/full/path.txt # blank if not available - clickable for vscode edit
Test Command: {TEST_COMMAND}
Test Result: {TEST_SUCCESS}
Auto Test: {AUTO_TEST} - Share Test Results: {INCLUDE_TEST_RESULTS}

The above menu will act as the template for Tests, Lint, and CMD menues

### CLI UI Test/Lint/CMD Menu
1. Run tests
2. [Add test results to prompt|Remove test results from prompt] # depending on current prompt state
3. Set test command and result
4. Turn [ON|OFF] auto test # depending on current AUTO_TEST value

### CLI UI Source Control Menu Header
- TBD
### CLI UI Source Control Menu 
- TBD
---

## vibedir.txt
The vibedir.txt file is generated from the codebase, dev.md, and other auxillary information needed in order to give na LLM all of the information needed to begin working with the developer. It is used on session init and refresh (for context window) in the cut/paste mode, and every time in API mode. 

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

The COMMANDS_AND_RESULTS will contain each command and its results that has been run and is set to be shared.

The TASK will be supplied if a task has been defined by the user (there may be times that the command results just speak for themselves)

#### Splitting vibedir.txt into vibedir_part1ofn.txt parts
If the user is in clipboard mode, then the vibedir.txt will be split into (~40k char) parts named vibedir_part1ofn.text in order to avoid truncation by the LLM UI. 

## Core Components

| Component | Role |
|---------|------|
| **`dev.md`** | Development guidelines, style, LLM behavior |
| **`prepdir`** | Clean, private, structured code output |
| **`applydir`** | Takes changes from LLM (in json described in CODE_CHANGE_INSTRUCTIONS) and applies them to the code base |
| **`fileclip`** | Clipboard control (for pasting files into UI) |
| **`vibedir`** | CLI based UI. UI orchestration, clipboard, token math |
| **`apibump`** | API client (includes LiteLLM wrapper), model metadata, context limits |

---

### Token Counting
- In CLIPBOARD mode, request tokens are counted for each generated prompt, and once 70% of the LLM context window has been reached, an automatic refresh will be triggered (where dev.md, code, and guidelines are reshared). We can also count tokens received in teh applydir.json file, but we have no way to count additional prompt information added by the user in the LLM UI, or additional response information outside of the applydir.json file.  
- In API mode, all prompt/response tokens can be counted. 

## Todo
- Build CLI menu selections and status items (test config, latest number of changes, latest commit message, latest token count)
- Build prompt - will create vibedir.txt when using API mode and vibedir_part1ofn.txt when using cut/paste mode. 
- Git integration (commit each change so can be reverted, flatten on pr?) - configurable (see config)
- Tests configuration
- Add token counting (tiktoken) in order to keep track of when to reshare dev.md, codebase for context (based on LLM context window)

---