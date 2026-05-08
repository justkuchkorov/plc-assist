# PLC Assist Demo Script

Target length: 60-90 seconds.

Public demo: https://plc-assist.onrender.com/

## Story

Generic LLMs can write PLC-looking code, but PLC engineers need CODESYS-style declarations, safety behavior, timer patterns, and reviewable outputs. PLC Assist is a focused AI tool for that workflow.

## Recording Flow

1. Open the app.
2. Click **Transformer cooling PID**.
3. Show the Requirement Builder fields and explain that users can specify equipment, inputs, outputs, faults, and safety/reset behavior instead of writing a perfect prompt.
4. Click **Generate Structured Text**.
5. Show the Local Validation panel:
   - score
   - declared variables
   - errors/warnings
   - fallback/repair badge if present
6. Scroll through the generated CODESYS Structured Text.
7. Click `.st` and `Report` download buttons.
8. End with the value proposition: PLC Assist does generation plus PLC-specific validation, not just generic code completion.

## Voiceover

> This is PLC Assist, an AI code assistant for industrial automation. Instead of asking a generic chatbot for PLC code, the user describes the equipment, inputs, outputs, faults, and safety behavior. PLC Assist generates IEC 61131-3 Structured Text for CODESYS, then runs local validation for common PLC-specific issues like undeclared variables, invalid CODESYS types, unsafe outputs, and suspicious timer or state-machine patterns. If the model fails or times out, it falls back to validated local patterns so the demo still returns useful starter code. The result is code, a variable table, an explanation, safety warnings, and downloadable `.st` and validation report files.

## Notes

- Keep the demo honest: say "local validation" rather than "guaranteed compile."
- Do not claim this is certified for real equipment.
- Strong phrase: "PLC-looking code is easy. PLC-reviewable code is the hard part."
