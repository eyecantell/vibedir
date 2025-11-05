# VibeDir - Functionality is not yet ready, but "COMING SOON" #

VibeDir is a utility to facilitate code modifications when using an AI assistant. It generates prompts for large language models to modify a codebase. VibeDir supports manual workflows (clipboard mode) and in the future will support API integration with the latest GenAI models.

## Overview  
`vibedir` enables **clipboard-driven UI** and **API-powered automation** for LLM development.
- Two modes of operation:  
  - **Clipboard**: Human-in-loop cut/paste to LLM UI (e.g. Grok, Claude, ChatGPT, other)
  - **API**: Uses `apibump` (LiteLLM wrapper) for scripted calls and usage charges.

<span style="color: red;">This text is red.</span>
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

### Config
    
    # The LLM is asked to provide a commit message for each set of changes. The following configures how that will be used.
    AUTO_COMMIT: true/false
    COMMIT_COMMAND: (e.g. git commit -a -m {message} )

    # Testing can be done automatically after each set of changes is successfully applied to the code base
    AUTO_TEST: true/false
    TEST_COMMAND: (e.g. pytest tests)

    AUTO_COMMAND: {optional command to be run after a code change is successfully applied}
    SHARE_AUTO_COMMAND_RESULTS: true/false

    LOGGING:
      LEVEL: "INFO"

    MODE: {CLIPBOARD or API, if API then LLM tag must be defined}
    CLIPBOARD_MAX_CHARS_PER_FILE: 40000 # set the max number of characters per file (to work around LLM UI file truncation)
    LLM:
      model: grok-4
      endpoint: https://api.x.ai/v1
      api_key: <todo: figure out how to store/retrieve this, maybe .netrc? What does LiteLLM do?>

### Token Counting
In clibboard mode, request tokens are counted for each generated prompt, and once 70% of the LLM context window has been reached, an automatic refresh will be triggered (where dev.md, code, and guidelines are reshared).
- In API mode, response tokens can be counted as well. 

## Todo
- Build CLI menu selections and status items (test config, latest number of changes, latest commit message, latest token count)
- Build prompt - will create vibedir.txt when using API mode and vibedir_part1ofn.txt when using cut/paste mode. 
- Git integration (commit each change so can be reverted, flatten on pr?) - configurable (see config)
- Tests configuration
- Add token counting (tiktoken) in order to keep track of when to reshare dev.md, codebase for context (based on LLM context window)

---