# Vibedir as a Pluggable Orchestration Layer: Recommended Approach

## Overview
Vibedir is designed as an orchestration tool for LLM-driven code development workflows, managing tasks like codebase preparation, prompt generation, change application, post-processing (e.g., linting, testing), and version control integration. To make vibedir truly flexible and future-proof—allowing components like codebase generation (currently handled by prepdir) or change application (handled by applydir) to be swapped with alternatives (e.g., Aider's methods or custom implementations)—implement a **pluggable architecture**.

This approach uses Python's **Abstract Base Classes (ABCs)** to define interfaces, **dynamic module importing** (via `importlib`) for runtime loading, and **configuration-driven selection** (via vibedir's TOML config) to specify plugins. For broader ecosystems, enhance with **entry points** from `setuptools` for automatic plugin discovery. This mirrors plugin systems in tools like pytest or Flask, enabling loose coupling while keeping vibedir's core workflow (e.g., menu-driven UI, hotkeys, revert handling) intact.

### Key Benefits
- **Decoupling**: Swap prepdir/applydir with Aider or others without rewriting vibedir.
- **Extensibility**: Users/third-parties can add plugins via config or packages.
- **Maintainability**: Interfaces enforce contracts; tests focus on abstractions.
- **Lightweight**: No heavy frameworks needed; built on stdlib.

### Potential Drawbacks
- Adds initial setup overhead (~100-200 lines).
- Requires careful error handling for missing plugins.
- If plugins proliferate, entry points add packaging complexity.

## Core Components of the Pluggable Design

### 1. Define Interfaces with ABCs
Use ABCs to abstract key functionalities. This acts like a contract: plugins must implement these methods.

- **Location**: Create a `vibedir/plugins/interfaces.py` module.
- **Examples**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, Any, List

  class CodebaseGenerator(ABC):
      """Interface for preparing codebase context for LLM prompts."""
      
      @abstractmethod
      def generate_output(self, base_dir: str, config: Dict[str, Any]) -> str:
          """Generate a codebase snapshot or context string."""
          pass
      
      @abstractmethod
      def add_files_to_context(self, files: List[str], config: Dict[str, Any]) -> str:
          """Dynamically add specific files to the context (Aider-inspired)."""
          pass

  class ChangeApplier(ABC):
      """Interface for applying LLM-generated code changes."""
      
      @abstractmethod
      def apply_changes(self, json_data: Dict[str, Any], base_dir: str, config: Dict[str, Any]) -> bool:
          """Apply changes from JSON; return True on success."""
          pass
      
      @abstractmethod
      def confirm_changes(self, json_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
          """Optional: Prompt user for confirmation before applying."""
          pass
  ```
- **Extension**: Add more ABCs as needed (e.g., `Linter`, `Tester`) for post-processing commands.

### 2. Implement Plugin Wrappers
Create concrete classes that wrap existing tools (e.g., prepdir, applydir, Aider). These are the "plugins."

- **Location**: Submodules like `vibedir/plugins/prepdir_wrapper.py`.
- **Example for Prepdir**:
  ```python
  from .interfaces import CodebaseGenerator
  from typing import Dict, Any, List

  class PrepdirGenerator(CodebaseGenerator):
      def __init__(self):
          try:
              from prepdir import generate_codebase_output
              self._generate_func = generate_codebase_output
          except ImportError:
              raise ImportError("prepdir required for this plugin.")

      def generate_output(self, base_dir: str, config: Dict[str, Any]) -> str:
          return self._generate_func(base_dir=base_dir, exclude=config.get("exclude_dirs", []))

      def add_files_to_context(self, files: List[str], config: Dict[str, Any]) -> str:
          # Implement or raise NotImplementedError if unsupported
          pass
  ```
- **For Aider (Future Replacement)**:
  ```python
  # vibedir/plugins/aider_wrapper.py
  import subprocess
  from .interfaces import CodebaseGenerator

  class AiderGenerator(CodebaseGenerator):
      def generate_output(self, base_dir: str, config: Dict[str, Any]) -> str:
          # Use subprocess to call Aider CLI or its library
          result = subprocess.run(["aider", "--read", base_dir], capture_output=True, text=True)
          if result.returncode != 0:
              raise RuntimeError("Aider failed.")
          return result.stdout  # Or process to extract context

      def add_files_to_context(self, files: List[str], config: Dict[str, Any]) -> str:
          # Aider-specific: Add files dynamically
          subprocess.run(["aider", "--add"] + files)
          return "Files added to Aider context."
  ```
- **Fallback Plugin**: Include a minimal built-in (e.g., simple file reader) for when dependencies are missing.

### 3. Config-Driven Plugin Selection
Use vibedir's TOML config to specify which plugin to load.

- **Config Snippet** (in `config.toml`):
  ```toml
  [plugins]
  codebase_generator = "vibedir.plugins.prepdir_wrapper.PrepdirGenerator"  # Dot-path to class
  change_applier = "vibedir.plugins.applydir_wrapper.ApplydirApplier"
  # Swap to: "vibedir.plugins.aider_wrapper.AiderApplier"
  ```
- **Loading Logic** (in vibedir's startup, e.g., `core.py`):
  ```python
  import importlib
  from typing import Type, Dict

  def load_plugin(dot_path: str) -> Type:
      module_name, class_name = dot_path.rsplit(".", 1)
      module = importlib.import_module(module_name)
      cls = getattr(module, class_name)
      if not issubclass(cls, RelevantABC):  # Check interface
          raise ValueError("Plugin does not implement required interface.")
      return cls

  # Usage
  config = load_config("vibedir")  # Your TOML loader
  generator_cls = load_plugin(config["plugins"]["codebase_generator"])
  generator = generator_cls()  # Instantiate; inject config if needed
  ```

### 4. Integrate into Vibedir's Workflow
- **Orchestration Loop**: Vibedir calls plugins at key points:
  ```python
  # vibedir/workflow.py (simplified)
  def run_workflow(config: Dict):
      generator = load_plugin(config["plugins"]["codebase_generator"])()
      applier = load_plugin(config["plugins"]["change_applier"])()
      
      codebase_context = generator.generate_output(base_dir=config["base_dir"], config=config)
      # ... Build LLM prompt, send/receive ...
      json_changes = llm_response["changes"]  # Parsed from LLM
      success = applier.apply_changes(json_changes, base_dir=config["base_dir"], config=config)
      
      if success:
          # Run post-processing commands (e.g., lint, test from config.toml)
          pass
  ```
- **Error Handling**: Wrap calls in try/except; fallback to built-in if plugin fails.

### 5. Advanced: Entry Points for Discovery
For user-contributed plugins:
- In `setup.py`:
  ```python
  entry_points={
      'vibedir.generators': ['prepdir = vibedir.plugins.prepdir_wrapper:PrepdirGenerator'],
  }
  ```
- Load:
  ```python
  from importlib.metadata import entry_points
  eps = entry_points(group='vibedir.generators')
  generator_cls = eps[config["plugins"]["codebase_generator_name"]].load()
  ```

### 6. Testing and Best Practices
- **Tests**: Use `unittest.mock` to patch `importlib`; test interfaces with `isinstance`.
- **Documentation**: Add a "Plugins" section in README.md with examples for custom plugins.
- **Migration Path**: Start with prepdir/applydir defaults; test Aider wrapper separately.

This design positions vibedir as a robust, adaptable orchestrator—ready for replacements like Aider while maintaining its unique strengths.