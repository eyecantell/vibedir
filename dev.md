# Paul Wessling – AI & Open-Source Dev Context
**Focus:** Commercial AI + open-source Python tools (APIs, pipelines, dev productivity)

## Workflow
- **Dev:** Windows/mac → **VSCode + Docker containers**
- **SCM/CI:** **GitHub + GitHub Actions** (test → PyPI publish)
- **AI Stack:** Ingest (API/Tika OCR) → Summarize (Grok/Claude/OpenAI) → Embed (SentenceTransformers) → Store (pgvector) → Serve (FastAPI) → Scale (Kafka/K8s/HPA) → UI (Flutter/Cloudflare)
- **Key Project:** **prepdir** (PyPI, 10k+ dl) – AI code prep: smart filtering, UUID scrubbing, YAML config, validation, structured output

## Strengths
- **Python:** FastAPI, Pydantic, Dynaconf, pytest, pdm
- **DevOps:** Docker, Skaffold/Helm, Prometheus/Grafana/Kafdrop
- **Reliability:** 100k+ unit C2 systems → informs scale/reproducibility, not direction

## Style
- Pithy, iterative, fast-learning, clarity-first

## LLM Guidance
- **Never guess code** – wait for actual files/functions
- **Design first** – for any non-trivial change (more than a simple bug fix), propose **architecture, components, data flow, interfaces** as applicable before coding  
- **Best tool for the job** – prefer proven open-source, but suggest better alternatives freely  
- **I love learning** – introduce new libraries/approaches when they clearly improve the solution  
- Assume GitHub + Actions workflow
- Suggest `devcontainer.json`, `pyproject.toml`, `docker-compose.yml`
- Keep responses concise; ask early clarifying questions
- Use modern AI/dev patterns – I adapt quickly

---

# Development Guidelines

- **Philosophy:** **Design → Implement** – no coding without a plan (except trivial fixes)  
- **Style:** **OO primary** (encapsulation, SRP), **FP for transforms/pipelines** → hybrid by default  

### Config
- Light: `os.getenv()` + `.env` (via `python-dotenv`)  
- Heavy: **Dynaconf + YAML** (custom → local → global → defaults)

### Logging
- `logging` stdlib (via `dictConfig`)  
- Open to `structlog`/`loguru` if complexity grows

### Errors
- **Exceptions** (rich, safe context)  
- Result objects only for retry/branch logic

### CLI
- **argparse** default  
- `typer`/`click` if subcommands or auto-docs needed

### Priorities
- **Design Upfront** – define scope, components, APIs, data model  
- Clarity > Cleverness  
- Reusability (CLI + lib dual interface)  
- Testability (pytest + containerized integration)  
- Privacy & Safety (UUID scrub, no PII in logs/examples)  
- **Open-Source First, But Flexible** – leverage community tools; replace with better fits when warranted

### Anti-Patterns
- God objects  
- Global state  
- Hardcoded paths/secrets  
- Unfiltered file dumps  
- Premature custom libraries  
- **Coding without design**

### LLM Code Hints
- Pydantic for config/API models  
- `dataclasses` or `NamedTuple` for immutable data  
- Pipeline: `extract → summarize → embed → store`  
- OO services: `Processor`, `Matcher`, `Ingestor`  
- Always include: **type hints**, **docstrings**, **CLI entrypoint**