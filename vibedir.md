# VibeDir - Functionality is not yet ready, but "COMING SOON" #

VibeDir is a utility to facilitate code modifications when using an AI assistant. It generates prompts for large language models to modify a codebase. VibeDir supports manual workflows (clipboard mode) and will soon support API integration with the latest GenAI models.

## Overview  
`vibedir` enables **clipboard-driven UI** and **API-powered automation** for LLM development.
- Two modes of operation:  
  - **Clipboard**: Human-in-loop cut/paste to LLM UI (e.g. Grok, Claude, ChatGPT, other)
  - **API**: Uses `apibump` (LiteLLM wrapper) for scripted calls and usage charges.

## CLI UI (in design phase)

### CLI UI Main Menu Header
- Current Prompt ('p') to [commit current changes and] [send|copy prompt to clipboard]
  - Errors: [Error encountered when applying latest changes.]
  - Results: [Tests⏳|✅|❌|�] - [Lint⏳|✅|❌|�] - [CMD⏳|✅|❌|�]
  - Auxillary: [n files] [dev.md]
  - Detected changes: file1, file2, ... # if manual changes detected
  - Task ('t' to [set|edit]): [blank|preview of current task wording...] 

- Other Results: [Changes⏳|✅|❌] - [Tests⏳|✅|❌|⊘] - [Lint⏳|✅|❌|⊘] - [CMD⏳|✅|❌|⊘]
- Legend: success✅ - running⏳ - failed❌ -  not run� - not configured⊘ 
         
- Menus: ('m') Test, Lint, CMD, Source Control settings
- Last commit: (Last commit message)
- Working commit: (Working commit message) # if current changes

### Notes on Main Menu Header fields:
The [commit current changes and] portion of the Current Prompt top message will be displayed if changes have been made (as detected by CHANGES_EXIST_RESULT) and AUTO_COMMIT is set to 'previous'.

The [send|copy prompt to clipboard] will be "send" if MODE = API, and "copy prompt to clipboard" if MODE = CLIPBOARD

Each of the Test, Lint, and CMD results will be shown in either the Results section (if INCLUDE_*_RESULTS=true) or the Other Results section (if INCLUDE_*_RESULTS=true). 
The icons next to each of Test, Link, CMD will be:
- ✅ if the configured *_COMMAND has run and *_SUCCESS yields true
- ❌ if the configured *_COMMAND has run and *_SUCCESS yields false
- ⏳ if the configured *_COMMAND is still running
- � if AUTO_* is set to false and the configured *_COMMAND has not been run manually
- ⊘ if the *_COMMAND value is not set
 
 Other Results: "Changes" will have icon:
  - ✅ if applydir applied the latest changes (applydir.json) successfully
  - ❌ if applydir encountered errors when applying the latest changes
  - ⏳ if the configured *_COMMAND is still running

### CLI UI Main Menu
1. Refresh info without action ('space bar')
2. [Set|Edit] prompt task ('p')  # Will be 'Set' if task is currently empty
3. Add files to prompt

3. Run tests ('t') # if TEST_COMMAND available
3. Re-run tests ('t') $ TEST_COMMAND available and test results available
4. Add Test Results to prompt # only if test results are available and not already in prompt

5. Run lint # if LINT_COMMAND available
5. Re-run lint # LINT_COMMAND available and lint results available
6. Add Linting Results # only if linting results are available and not already in prompt
5. Run CMD # if CMD_COMMAND available
5. Add CMD Results # only if AUTO_COMMAND results are available and not already in prompt
6. Run command ('R') and include output in prompt ('r')
7. Revert most recent changes [requires REVERT_CHANGES_COMMAND, CHANGES_EXIST_COMMAND, CHANGES_EXIST_RESULT] # only if changes have been made since last commit (CHANGES_EXIST_RESULT)

### CLI UI Test/Lint/CMD Menu Header
Test results in prompt: [Yes|No]
Result: [success✅|running⏳|failed❌|not run�]
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

    [TEST_RESULTS]
    {test command and results if tests have been run}
    [/TEST_RESULTS]

    [LINT_RESULTS]
    {test command and results if tests have been run}
    [/LINT_RESULTS]

    [OTHER_RESULTS]
    {auto-command and results if configured to be shared}
    [/OTHER_RESULTS]

    [TASK]
    {User supplied task, note they can alternately type into the LLM window if using cut/paste mode}
    [/TASK]
  ```

The DEV_GUIDELINES, CODEBASE, and CODE_CHANGE_INSTRUCTIONS will be included on session start or refresh. 

The TEST_RESULTS will be supplied if tests have been run.

The OTHER_RESULTS will be supplied if SHARE_AUTO_COMMAND_RESULTS is true

The TASK will be supplied if a task has been defined by the user

#### Splitting vibedir.txt into vibedir_part1ofn.txt parts
If the user is in clipboard mode, then the vibedir.txt will be split into (~40k char) parts named vibedir_part1ofn.text in order to avoid truncation by the LLM UI. 

## Core Components

| Component | Role |
|---------|------|
| **`dev.md`** | Development guidelines, style, LLM behavior |
| **`prepdir`** | Clean, private, structured code output |
| **`applydir`** | Takes changes from LLM (in json) and applies them to the code base |
| **`fileclip`** | Clipboard control (for pasting files into UI) |
| **`vibedir`** | CLI based UI. UI orchestration, clipboard, token math |
| **`apibump`** | API client, model metadata, context limits |

---

## WorkFlow (Clipboard Mode)

### User runs: vibedir CLI from the working directory
1. CLI menu pops up with options to:
  - Start new session (or refresh session)
    - User generates question/command for LLM (either in vibedir to be pasted or in the LLM UI)
    - Generate vibedir_part1ofn.text files and copy to clipboard
    - User pastes the command and vibedir context information into LLM UI.

  - On LLM answer
    - LLM UI answers with applydir json format. 
    - User saves applydir.json to working directory and it is automatically applied to the codebase (vibedir watching for file)
    - If auto_commit is configured then commit command is run.
    - If auto_test is configured then tests are run
    - if auto_command is set it is run

  - User defines additional tasks and pastes into LLM UI (opr writes directly in LLM UI)
  - Additional results are applied

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