import argparse
import logging
import os
import sys
from typing import Optional

from openai import OpenAI

from vibedir.config import load_config


def setup_logging(config, handler: logging.Handler = None) -> None:
    """Configure logging based on config settings."""
    log_level = getattr(logging, config.LOGGING.LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    # Remove existing handlers to avoid duplicates
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    # Add provided handler or default to StreamHandler
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


def build_prompt(prepped_dir_path: str, user_request: str, config) -> str:
    """Construct a prompt for the LLM based on prepped_dir.txt and user request."""
    try:
        with open(prepped_dir_path, "r", encoding="utf-8") as f:
            prepped_dir_content = f.read()
    except Exception as e:
        logging.error(f"Failed to read {prepped_dir_path}: {e}")
        raise

    prompt_template = config.get("prompt_template")
    return prompt_template.format(
        user_request=user_request,
        prepped_dir_content=prepped_dir_content,
    )


def validate_llm_response(content: str) -> None:
    """Validate that the LLM response contains required file markers."""
    if not all(marker in content for marker in ["Begin File", "End File"]):
        raise ValueError("Invalid LLM response: missing required file markers")


def call_llm_api(prompt: str, config) -> str:
    """Send prompt to the configured LLM and return modified_prepped_dir.txt content."""
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "grok")
    endpoint = llm_config.get("endpoint", "https://api.x.ai/v1")
    api_key = llm_config.get("api_key")
    model = llm_config.get("model", "grok-3")

    if not api_key:
        raise ValueError("LLM API key not provided in config")

    client = OpenAI(base_url=endpoint, api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a code modification assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        validate_llm_response(content)
        return content
    except Exception as e:
        logging.error(f"Failed to call LLM API: {e}")
        raise


def save_output(content: str, output_path: str) -> None:
    """Save LLM's output to the specified file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Saved output to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save output to {output_path}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Interact with an LLM to modify prepped_dir.txt.")
    parser.add_argument("prepped_dir", help="Path to prepped_dir.txt from prepdir")
    parser.add_argument("--output", default="modified_prepped_dir.txt", help="Output file for modified content")
    parser.add_argument("--request", required=True, help="Change request for the LLM (e.g., 'Refactor test_file.py')")
    parser.add_argument("--manual", action="store_true", help="Output prompt for manual editing instead of API call")
    parser.add_argument("--config", default="src/vibedir/config.yaml", help="Path to configuration file")
    args = parser.parse_args()

    # Load configuration
    config = load_config("vibedir", args.config)
    setup_logging(config)

    # Build prompt
    prompt = build_prompt(args.prepped_dir, args.request, config)

    if args.manual:
        print("=== Prompt for LLM ===")
        print(prompt)
        print("=== End Prompt ===")
        print(f"Please save the LLM's output as {args.output}")
    else:
        # Call LLM API
        modified_content = call_llm_api(prompt, config)
        # Save output
        save_output(modified_content, args.output)


if __name__ == "__main__":
    main()