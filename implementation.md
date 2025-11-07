Vibedir Design Decisions 2025-11-06
Overview
This document captures the refined design decisions for the vibedir CLI project, based on discussions around state persistence, configuration management, CLI UI, prompt generation, and integrations. It follows the philosophy from dev.md: design upfront, clarity-first, OO primary with FP elements, best tool for the job (e.g., Pydantic for models, Dynaconf optional for merging if needed later). Key goals: Lightweight, session-persistent state, configurable via YAML/JSON, safe subprocess handling, and alignment with vibedir.md workflows (clipboard/API modes, auto-commands, token counting).
Decisions are grouped by category. This is version 1.0 as of November 6, 2025.
Architecture Components

Models (Pydantic): Used for validation, serialization, and type safety. Two main models: VibedirConfig (immutable defaults + session changes) and VibedirState (runtime/session data).
Managers (OO Classes):

ConfigManager: Handles loading (YAML defaults + JSON overrides) and saving (to JSON).
StateManager: Load/save state JSON; includes refresh_dynamics() for non-persisted fields (e.g., last commit).
ResultsHandler: Executes commands safely, writes to result files, evaluates success, updates state.


Persistence Layer:

Directory: Hardcoded .vibedir/ relative to CWD (launch dir). No env var or git-root detection—assumes consistent launch from project root to avoid subproject conflicts.
Files:

.vibedir/config.yaml: User-editable defaults (optional; falls back to model defaults).
.vibedir/config.json: Session changes (always loaded/applied on start; overwrites YAML in memory).
.vibedir/state.json: Runtime state.
.vibedir/results/: Single output files (e.g., test_output.txt, lint_output.txt, cmd_output.txt)—overwritten on re-run; no history or cleanup.




No ALWAYS_LOAD_SESSION_CONFIG: Removed for simplicity. Always load/apply session JSON (true behavior by default).

Data Models
VibedirConfig (Single Model for Config + Session Changes)
Pydantic BaseModel with defaults from vibedir.md. Loaded from YAML (defaults), merged/overwritten by JSON. Saved as full config to JSON on changes.
pythonfrom pydantic import BaseModel, Field
from typing import Literal, Optional, Dict
```
class VibedirConfig(BaseModel):
    mode: Literal["CLIPBOARD", "API"] = "CLIPBOARD"
    clipboard_max_chars_per_file: int = 40000
    llm: Optional[Dict[str, str]] = None  # e.g., {"model": "grok-4", "endpoint": "..."}
    ask_llm_for_commit_message: bool = True  # Renamed from ENABLE_SOURCE_CONTROL; toggles commit-msg requests for token savings
    auto_commit: Literal["previous", "latest", "off"] = "off"  # Safe default
    commit_command: str = "git commit -a -m {{commit_message}}"
    revert_changes_command: str = "git checkout -- . && git reset"
    last_commit_message_command: str = "git log -n 1 | egrep -v '^[A-z]|^\s*$'"
    changes_exist_command: str = "git diff --quiet HEAD"
    changes_exist_result: Literal["EXIT_CODE"] = "EXIT_CODE"
    auto_diff: bool = False
    diff_command: str = "git diff"
    auto_test: bool = False
    test_command: str = "pytest tests"
    test_success: str = "EXIT_CODE"  # Flexible; add SUCCESS_PATTERN (e.g., grep) if needed
    share_test_results: bool = False
    auto_lint: bool = False
    lint_command: str = "ruff check {{ base_directory }}"
    lint_success: str = "EXIT_CODE"
    share_lint_results: bool = False
    auto_cmd: bool = False
    cmd_command: str = "ruff format {{ base_directory }}"
    share_cmd_results: bool = False
    logging: Dict[str, str] = Field(default_factory=lambda: {"LEVEL": "INFO"})
```

VibedirState (Runtime/Session Data)
Pydantic BaseModel; persisted in .vibedir/state.json. No dynamic fields (e.g., last_commit)—refreshed on-demand.

```
pythonfrom pydantic import BaseModel, Field
from typing import Optional, Dict, List
from pathlib import Path

class VibedirState(BaseModel):
    task: Optional[str] = None
    auxiliary: Dict[str, str | int] = Field(default_factory=dict)  # e.g., {"file_count": 5, "dev_md": "ready", "tests": "ready"}
    add_test_results_to_prompt: bool = False
    test_success: Optional[bool] = None
    test_result_file: Optional[Path] = None  # Relative to .vibedir/results/
    add_lint_results_to_prompt: bool = False
    lint_success: Optional[bool] = None
    lint_result_file: Optional[Path] = None
    add_cmd_results_to_prompt: bool = False
    cmd_success: Optional[bool] = None
    cmd_result_file: Optional[Path] = None
    add_manual_changes: List[str] = Field(default_factory=list)  # File paths if detected
    token_count: int = 0
```
Data Flow and Operations

CLI Startup:

Create .vibedir/ if missing.
ConfigManager.load(): Read YAML defaults → Merge/overwrite from config.json (always).
StateManager.load(): Read state.json → refresh_dynamics() (run commands for last_commit, changes_exist, working_commit).


User Actions:

Toggle config (e.g., AUTO_TEST): Update in-memory config → Save to config.json on exit or key events.
Run command (e.g., tests): ResultsHandler.execute(test_command) → Write to test_output.txt (overwrite) → Eval success (EXIT_CODE default) → Update state → Save state.json.


Prompt Generation:

Build vibedir.txt with sections (e.g., [TEST_RESULTS] if share_test_results and add_to_prompt).
Clipboard mode: Split into parts on chars (CLIPBOARD_MAX_CHARS_PER_FILE).
Token counting: tiktoken on emitted text; refresh at 70% context (warn on user-added uncertainty in clipboard).


Exit: Final save of config.json and state.json.

CLI UI Decisions

Header/Menu: As in vibedir.md (e.g., status emojis: ✅/⏳/❌/�; menus for Test/Lint/CMD/Source Control).
Keys: Single-letter (e.g., 't' set task, 'T' Test menu, 'r'/'R' run/include command). Add 'r' shortcut for full refresh (dynamics + menu render).
Paths: Display result files as vscode://file/{abs_path} for clickable in VSCode terminal (fallback to plain if not VSCode).
Conditionals: Hide items if commands unavailable (e.g., no TEST_COMMAND → no Run Test menu item). If !ask_llm_for_commit_message, disable commit-related features/menus for token savings.
Source Control: Always available manual revert/diff if git present; auto features toggled separately.

Integrations and Safety

Subprocess Handling: Use shlex.split + list args (e.g., subprocess.run(cmd_list, cwd=base_dir, timeout=300)). Replace {{base_directory}} safely. Eval success with EXIT_CODE (default); optional SUCCESS_PATTERN (grep output).
Git/Source Control: Conditional on ask_llm_for_commit_message (ask LLM for msgs if true). Dynamics via commands (e.g., CHANGES_EXIST_COMMAND); run on refresh.
Token Math: Separate from splitting—tiktoken for context refresh threshold.
Error Handling: Rich exceptions; log via stdlib (dictConfig). No global state.
Testability: Injectable Executor protocol (default: SubprocessExecutor; mock for pytest).
Future Hooks: Plugin registry for custom result types (e.g., coverage); but keep minimal now.