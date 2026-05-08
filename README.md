# PLC Assist

AI-assisted IEC 61131-3 Structured Text generation for CODESYS, with local validation and demo-safe fallback patterns.

PLC Assist is built around a simple idea: generic LLMs can produce PLC-looking code, but industrial automation engineers need code that is structured, declared, safety-aware, and reviewable. PLC Assist turns requirements into Structured Text, validates common PLC-specific failure modes, and returns code with a variable table, explanation, warnings, and a validation report.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/justkuchkorov/plc-assist)

## Why This Exists

Writing Structured Text from scratch is slow and error-prone. Generic chatbots often produce code that will not compile in CODESYS: wrong data types, missing declarations, weak safety behavior, or suspicious timer/state-machine logic.

PLC Assist is a narrow tool for industrial automation workflows. It is intended to become the "DeepL for PLC code": specialized, structured, and more reliable than a general-purpose model for this one job.

## What It Does

- Generates IEC 61131-3 Structured Text for CODESYS.
- Guides users with categories and a structured Requirement Builder.
- Uses category templates and curated few-shot examples for PID, motor, valve, and state-machine logic.
- Validates generated code for local PLC-specific issues.
- Runs one AI repair pass if validation fails.
- Falls back to local validated patterns when Gemini is unavailable, slow, or still fails validation.
- Exports generated code as `.st`.
- Exports a validation report as `.txt`.

## Validation Checks

PLC Assist currently checks for:

- missing `PROGRAM` / `FUNCTION_BLOCK` structure
- unbalanced `IF`, `CASE`, loop, and `VAR` blocks
- undeclared identifiers
- invalid CODESYS data types such as `float` or lowercase `int`
- assignment mistakes such as `=` instead of `:=`
- missing semicolons in likely statement lines
- missing safety patterns for physical outputs
- suspicious state-machine patterns, including timer member assignment and timer self-reference

This is not a replacement for a real CODESYS compiler or PLC engineer review. It is a quality gate that catches common LLM mistakes before the user sees the output.

## Demo Flow

1. Open the app.
2. Choose **PID Control Loop** or click **Transformer cooling PID**.
3. Optionally use the Requirement Builder to specify equipment, inputs, outputs, faults, and reset behavior.
4. Generate Structured Text.
5. Review the Local Validation panel.
6. Download the `.st` file and validation report.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Flask |
| LLM | Gemini 2.5 Flash |
| Production server | Gunicorn |
| Prompts | IEC rules + CODESYS rules + safety rules |
| Templates | Category-specific Markdown templates |
| Examples | Curated few-shot ST patterns |
| Frontend | Vanilla HTML/CSS/JS |
| Deployment | Render-ready `render.yaml` |

## Architecture

```text
Browser UI
  -> POST /generate
  -> generator.py
  -> Gemini call with timeout
  -> parse CODE / VARIABLES / EXPLANATION / WARNINGS
  -> validator.py local checks
  -> optional AI repair pass
  -> fallback pattern if model unavailable or still invalid
  -> JSON response
  -> UI renders code, validation, report, downloads
```

## Quick Start

```bash
git clone https://github.com/justkuchkorov/plc-assist.git
cd plc-assist
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_key_here
```

Run locally:

```bash
python app.py
```

Open `http://localhost:5001`.

If `GEMINI_API_KEY` is not set, the app still works in local fallback mode for supported categories.

## Deploy On Render

The repo includes `render.yaml`.

Render settings:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Health check: `/healthz`
- Optional secret: `GEMINI_API_KEY`
- Optional demo setting: `PLC_ASSIST_DEMO_MODE=1`

Without `GEMINI_API_KEY`, or with `PLC_ASSIST_DEMO_MODE=1`, the public demo still returns validated local fallback patterns.

## Project Structure

```text
plc-assist/
├── app.py              Flask app, routes, categories, prompt ideas
├── config.py           API key + model config
├── generator.py        LLM generation, repair loop, fallback routing
├── validator.py        Local Structured Text validation
├── fallbacks.py        Local validated demo patterns
├── examples/           Few-shot examples injected by category
├── prompts/            System, CODESYS, and safety rules
├── templates/          Web UI and generation templates
├── static/             Frontend JS/CSS
├── test_validator.py   Focused validator tests
├── render.yaml         Render deployment blueprint
└── requirements.txt    Python dependencies
```

## Roadmap

- [x] Local validation
- [x] AI repair pass
- [x] Local fallback patterns
- [x] Structured Requirement Builder
- [x] `.st` and validation report downloads
- [x] Few-shot examples for PID, motor, valve, and state machines
- [ ] Public demo deployment
- [ ] Evaluation benchmark across 20-50 PLC prompts
- [ ] Code Review mode for existing Structured Text
- [ ] CODESYS compile/export readiness
- [ ] Siemens TIA Portal / SCL support

## Safety Note

Generated code must be reviewed and tested in CODESYS before being used on real equipment. PLC Assist is a coding assistant and validation layer, not a certified safety system.

## License

MIT
