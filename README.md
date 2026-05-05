# PLC Assist

AI-powered IEC 61131-3 Structured Text code generator for CODESYS. Describe what you need in plain English — get production-ready PLC code with variable tables, logic explanations, and safety warnings.

## Why This Exists

Writing Structured Text from scratch is slow and error-prone. Generic LLMs produce code that won't compile in CODESYS — wrong data types, missing declarations, no safety logic. PLC Assist is purpose-built for industrial automation: every output follows IEC 61131-3 standards, CODESYS naming conventions, and real-world safety practices.

## Features

- **6 specialized categories** — PID control, motor control, state machines, alarm handling, valve control, or general/custom
- **Template-guided generation** — each category has a domain-specific template that ensures correct structure
- **Safety-first** — emergency stops, fail-safe defaults, interlocks, and sensor validation baked in
- **CODESYS V3.5+ compatible** — proper `PROGRAM`/`FUNCTION_BLOCK` structure, correct types (`REAL` not `float`), standard library FBs (TON, TOF, R_TRIG, etc.)
- **Structured output** — code + variable table + step-by-step explanation + safety warnings
- **Retry logic** — handles Gemini API rate limits with exponential backoff

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Flask (Python) |
| LLM | Gemini 2.5 Flash |
| Prompts | 3-layer system (IEC rules + CODESYS specifics + safety rules) |
| Templates | Category-specific MD files guiding output structure |
| Frontend | Vanilla HTML/CSS/JS with Material Icons |

## Quick Start

```bash
git clone https://github.com/justkuchkorov/plc-assist.git
cd plc-assist
pip install flask google-genai python-dotenv
```

Create `.env`:
```
GEMINI_API_KEY=your_key_here
```

Run:
```bash
python app.py
```

Open `http://localhost:5001` — pick a category, describe your requirement, get code.

## Example

**Input:** "PID controller for tank water level. Setpoint 75%, 4-20mA level transmitter input, control output to proportional valve CV-101. Alarm at 90% high and 10% low."

**Output:** Complete FUNCTION_BLOCK with PID logic, analog scaling, alarm comparators, variable declarations table, and safety warnings about sensor failure modes.

## Project Structure

```
plc-assist/
├── app.py              Flask app — routes, categories, examples
├── config.py           API key + model config
├── generator.py        Gemini code generation + response parsing
├── prompts/
│   ├── system.md       IEC 61131-3 rules, naming conventions, output format
│   ├── codesys.md      CODESYS-specific rules
│   └── safety.md       Safety rules for industrial code
├── templates/
│   ├── index.html      Web UI
│   ├── pid_loop.md     PID template
│   ├── motor_control.md
│   ├── state_machine.md
│   ├── alarm_handler.md
│   └── valve_control.md
└── static/
    ├── script.js
    └── style.css
```

## Roadmap

- [ ] Syntax validation (compile-check before returning)
- [ ] Few-shot examples from real industrial projects
- [ ] Export to CODESYS `.export` format
- [ ] Multi-language input (describe in any language, get ST code)
- [ ] Code review mode (paste existing ST, get improvement suggestions)

## License

MIT
