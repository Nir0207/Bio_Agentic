# runbook

## Answer a Sample Payload

```bash
cd answering
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m answering.app.cli run all
```

## Switch Providers

Set provider env values and run:

```bash
ANSWERING_PROVIDER=ollama \
ANSWERING_MODEL_NAME=llama3.1 \
OLLAMA_BASE_URL=http://host.docker.internal:11434 \
python -m answering.app.cli answer sample
```

Other supported values for `ANSWERING_PROVIDER`:
- `openai_compatible`
- `azure_openai`
- `anthropic_compatible`

## Enable Fallback Mode

```bash
ANSWERING_USE_FALLBACK_ONLY=true python -m answering.app.cli run all
```

## Common Formatting Failures

1. Missing citations in rendered text
- check supporting evidence ids in verified payload
- ensure claim status is `supported` or `partially_supported`

2. Unsupported claims appearing in answer
- verify claim filter in `services/prompt_builder.py`
- verify answer renderer only renders supported statuses

3. Appendix missing graph-path details
- verify graph evidence ids exist in claim verdicts
- optional enrichment requires reachable Neo4j connection and credentials
