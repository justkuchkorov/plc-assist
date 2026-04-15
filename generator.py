import os
import re
import time
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Load prompt files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

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


def generate_st_code(description: str, category: str = "general") -> dict:
    """Generate IEC 61131-3 Structured Text from a natural language description."""

    if not client:
        return {
            "error": "GEMINI_API_KEY not set. Create a .env file with your key.",
            "code": "",
            "variables": "",
            "explanation": "",
            "warnings": "",
        }

    system_prompt = _load_prompts()
    template = _load_template(category)

    user_prompt = f"Generate CODESYS IEC 61131-3 Structured Text code for the following requirement:\n\n{description}"
    if template:
        user_prompt += f"\n\nUse this template as a guide for the structure and required elements:\n\n{template}"

    # Retry with backoff for rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.3,
                },
            )
            parsed = _parse_response(response.text)
            parsed["raw"] = response.text
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
            return {
                "error": error_str,
                "code": "",
                "variables": "",
                "explanation": "",
                "warnings": "",
            }
