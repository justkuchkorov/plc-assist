import os
import queue
import re
import threading
import time
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from fallbacks import build_fallback_result, infer_category
from validator import format_issues_for_prompt, mark_repaired, validate_st_code

# Load prompt files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")
MODEL_TIMEOUT_SECONDS = 35

# Initialize client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_prompts() -> str:
    system = _load_file(os.path.join(PROMPTS_DIR, "system.md"))
    codesys = _load_file(os.path.join(PROMPTS_DIR, "codesys.md"))
    safety = _load_file(os.path.join(PROMPTS_DIR, "safety.md"))
    return f"{system}\n\n{codesys}\n\n{safety}"


def _load_template(category: str) -> str:
    template_map = {
        "pid_loop": "pid_loop.md",
        "motor_control": "motor_control.md",
        "state_machine": "state_machine.md",
        "alarm_handler": "alarm_handler.md",
        "valve_control": "valve_control.md",
    }
    filename = template_map.get(category)
    if filename:
        path = os.path.join(TEMPLATES_DIR, filename)
        if os.path.exists(path):
            return _load_file(path)
    return ""


def _load_examples(category: str) -> str:
    example_map = {
        "pid_loop": "pid_loop.md",
        "motor_control": "motor_control.md",
        "state_machine": "state_machine.md",
        "valve_control": "valve_control.md",
    }
    filename = example_map.get(category)
    if not filename:
        return ""

    path = os.path.join(EXAMPLES_DIR, filename)
    if os.path.exists(path):
        return _load_file(path)
    return ""


def _parse_response(text: str) -> dict:
    """Parse the LLM response into sections."""
    sections = {"code": "", "variables": "", "explanation": "", "warnings": ""}

    # Extract CODE section
    code_match = re.search(
        r"### CODE\s*```(?:iec|st|structured[_ ]?text)?\s*\n(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if code_match:
        sections["code"] = code_match.group(1).strip()

    # Extract VARIABLES section
    var_match = re.search(
        r"### VARIABLES\s*\n(.*?)(?=### |\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if var_match:
        sections["variables"] = var_match.group(1).strip()

    # Extract EXPLANATION section
    exp_match = re.search(
        r"### EXPLANATION\s*\n(.*?)(?=### |\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if exp_match:
        sections["explanation"] = exp_match.group(1).strip()

    # Extract WARNINGS section
    warn_match = re.search(
        r"### WARNINGS\s*\n(.*?)(?=### |\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if warn_match:
        sections["warnings"] = warn_match.group(1).strip()

    # Fallback: if parsing failed, put everything in code
    if not sections["code"] and text.strip():
        sections["code"] = text.strip()

    return sections


def _generate_content(user_prompt: str, system_prompt: str) -> str:
    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def run_request() -> None:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.3,
                },
            )
            result_queue.put(("ok", response.text))
        except Exception as exc:
            result_queue.put(("error", exc))

    thread = threading.Thread(target=run_request, daemon=True)
    thread.start()

    try:
        status, payload = result_queue.get(timeout=MODEL_TIMEOUT_SECONDS)
    except queue.Empty as exc:
        raise TimeoutError("Model request timed out.") from exc

    if status == "error":
        raise payload
    return payload


def _build_repair_prompt(original_description: str, category: str, parsed: dict, validation: dict) -> str:
    return f"""The Structured Text you generated did not pass PLC Assist validation.

Original requirement:
{original_description}

Category:
{category}

Validation issues:
{format_issues_for_prompt(validation)}

Current output sections:

### CODE
```iec
{parsed.get("code", "")}
```

### VARIABLES
{parsed.get("variables", "")}

### EXPLANATION
{parsed.get("explanation", "")}

### WARNINGS
{parsed.get("warnings", "")}

Repair the output so it follows valid IEC 61131-3 Structured Text for CODESYS.
Keep the same exact response format: ### CODE, ### VARIABLES, ### EXPLANATION, ### WARNINGS.
Do not remove safety behavior to satisfy validation; declare missing variables and fix syntax instead."""


def generate_st_code(description: str, category: str = "general") -> dict:
    """Generate IEC 61131-3 Structured Text from a natural language description."""

    effective_category = infer_category(description, category)

    if not client:
        return build_fallback_result(
            description,
            effective_category,
            "GEMINI_API_KEY is not set, so PLC Assist returned a local validated pattern.",
        )

    system_prompt = _load_prompts()
    template = _load_template(effective_category)
    examples = _load_examples(effective_category)

    user_prompt = f"Generate CODESYS IEC 61131-3 Structured Text code for the following requirement:\n\n{description}"
    if template:
        user_prompt += f"\n\nUse this template as a guide for the structure and required elements:\n\n{template}"
    if examples:
        user_prompt += f"\n\nStudy these verified PLC Assist examples for style and safety patterns. Do not copy them blindly; adapt the pattern to the user requirement:\n\n{examples}"

    # Retry with backoff for rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            text = _generate_content(user_prompt, system_prompt)
            parsed = _parse_response(text)
            parsed["raw"] = text
            parsed["repaired"] = False
            parsed["effective_category"] = effective_category
            parsed["validation"] = validate_st_code(parsed.get("code", ""), description, effective_category)

            if parsed["validation"]["status"] == "needs_repair":
                try:
                    repair_prompt = _build_repair_prompt(description, effective_category, parsed, parsed["validation"])
                    repaired_text = _generate_content(repair_prompt, system_prompt)
                    repaired = _parse_response(repaired_text)
                    repaired["raw"] = repaired_text
                    repaired["repaired"] = True
                    repaired["validation"] = mark_repaired(
                        validate_st_code(repaired.get("code", ""), description, effective_category)
                    )
                    repaired["effective_category"] = effective_category

                    # Only use the repaired version if it is strictly better.
                    if repaired["validation"]["score"] >= parsed["validation"]["score"]:
                        if repaired["validation"]["status"] != "needs_repair":
                            return repaired
                        return build_fallback_result(
                            description,
                            effective_category,
                            "Model output still failed validation after repair, so PLC Assist returned a local validated pattern.",
                        )
                except Exception as repair_error:
                    parsed["repair_error"] = str(repair_error)

                return build_fallback_result(
                    description,
                    effective_category,
                    "Model output failed validation, so PLC Assist returned a local validated pattern.",
                )

            return parsed
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 20
                    time.sleep(wait)
                    continue
                return {
                    "error": f"Rate limited by Gemini API. Free tier allows ~15 requests/minute. Wait a moment and try again.",
                    "code": "",
                    "variables": "",
                    "explanation": "",
                    "warnings": "",
                }
            if "503" in error_str or "UNAVAILABLE" in error_str:
                return build_fallback_result(
                    description,
                    effective_category,
                    "Gemini is temporarily unavailable, so PLC Assist returned a local validated pattern.",
                )
            if "timed out" in error_str.lower():
                return build_fallback_result(
                    description,
                    effective_category,
                    "Gemini took too long to respond, so PLC Assist returned a local validated pattern.",
                )
            return {
                "error": _friendly_error(error_str),
                "code": "",
                "variables": "",
                "explanation": "",
                "warnings": "",
            }


def _friendly_error(error: str) -> str:
    if "503" in error or "UNAVAILABLE" in error:
        return "The model is temporarily busy. Try again in a minute."
    return error
