import re
from dataclasses import dataclass


IEC_TYPES = {
    "BOOL",
    "BYTE",
    "WORD",
    "DWORD",
    "LWORD",
    "SINT",
    "USINT",
    "INT",
    "UINT",
    "DINT",
    "UDINT",
    "LINT",
    "ULINT",
    "REAL",
    "LREAL",
    "TIME",
    "DATE",
    "TOD",
    "TIME_OF_DAY",
    "DT",
    "DATE_AND_TIME",
    "STRING",
    "WSTRING",
}

STANDARD_FBS = {"TON", "TOF", "TP", "CTU", "CTD", "CTUD", "SR", "RS", "R_TRIG", "F_TRIG"}

KEYWORDS = {
    "PROGRAM",
    "END_PROGRAM",
    "FUNCTION_BLOCK",
    "END_FUNCTION_BLOCK",
    "FUNCTION",
    "END_FUNCTION",
    "VAR",
    "VAR_INPUT",
    "VAR_OUTPUT",
    "VAR_IN_OUT",
    "VAR_TEMP",
    "VAR CONSTANT",
    "VAR_GLOBAL",
    "END_VAR",
    "IF",
    "THEN",
    "ELSIF",
    "ELSE",
    "END_IF",
    "CASE",
    "OF",
    "END_CASE",
    "FOR",
    "TO",
    "BY",
    "DO",
    "END_FOR",
    "WHILE",
    "END_WHILE",
    "REPEAT",
    "UNTIL",
    "END_REPEAT",
    "TRUE",
    "FALSE",
    "AND",
    "OR",
    "NOT",
    "XOR",
    "MOD",
    "RETURN",
    "EXIT",
}

STANDARD_FUNCTIONS = {
    "ABS",
    "ACOS",
    "ASIN",
    "ATAN",
    "COS",
    "EXP",
    "LN",
    "LOG",
    "MAX",
    "MIN",
    "LIMIT",
    "SEL",
    "SIN",
    "SQRT",
    "TAN",
    "CONCAT",
    "LEN",
    "LEFT",
    "RIGHT",
    "MID",
    "BOOL_TO_INT",
    "INT_TO_REAL",
    "REAL_TO_INT",
    "DINT_TO_REAL",
    "REAL_TO_DINT",
}

STANDARD_FB_PARAMETERS = {
    "IN",
    "PT",
    "ET",
    "Q",
    "CLK",
    "CU",
    "CD",
    "RESET",
    "LOAD",
    "PV",
    "CV",
    "S",
    "R",
    "SET1",
    "RESET1",
}

INVALID_TYPE_HINTS = {
    "float": "Use REAL or LREAL instead of float.",
    "double": "Use LREAL instead of double.",
    "boolean": "Use BOOL instead of boolean.",
    "integer": "Use INT or DINT instead of integer.",
    "int": "Use INT or DINT instead of int.",
    "string": "Use STRING with uppercase type spelling.",
}


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict:
        data = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.line is not None:
            data["line"] = self.line
        return data


def validate_st_code(code: str, description: str = "", category: str = "general") -> dict:
    """Run lightweight IEC 61131-3/CODESYS checks on generated Structured Text."""
    issues: list[Issue] = []
    clean_code = _strip_comments(code or "")
    lines = clean_code.splitlines()

    if not code or not code.strip():
        issues.append(Issue("error", "empty_code", "No Structured Text code was generated."))
        return _result(issues, declared={}, used=set(), repaired=False)

    _check_program_structure(clean_code, issues)
    _check_block_balance(lines, issues)
    declared, declaration_types = _parse_declarations(clean_code, issues)
    used = _extract_used_identifiers(clean_code, declared)
    _check_undeclared_identifiers(declared, declaration_types, used, issues)
    _check_bad_types(lines, issues)
    _check_assignment_syntax(lines, issues)
    _check_semicolons(lines, issues)
    _check_safety_patterns(clean_code, description, category, issues)

    return _result(issues, declared=declared, used=used, repaired=False)


def mark_repaired(validation: dict) -> dict:
    validation = dict(validation)
    validation["repaired"] = True
    return validation


def format_issues_for_prompt(validation: dict) -> str:
    if not validation.get("issues"):
        return "No validation issues."

    lines = []
    for issue in validation["issues"]:
        location = f"line {issue['line']}: " if "line" in issue else ""
        lines.append(f"- {issue['severity'].upper()} {issue['code']}: {location}{issue['message']}")
    return "\n".join(lines)


def _check_program_structure(code: str, issues: list[Issue]) -> None:
    has_program = re.search(r"\bPROGRAM\s+\w+", code, re.IGNORECASE)
    has_fb = re.search(r"\bFUNCTION_BLOCK\s+\w+", code, re.IGNORECASE)
    has_function = re.search(r"\bFUNCTION\s+\w+", code, re.IGNORECASE)

    if not (has_program or has_fb or has_function):
        issues.append(
            Issue(
                "error",
                "missing_pou",
                "Code should start with PROGRAM, FUNCTION_BLOCK, or FUNCTION.",
            )
        )

    if has_program and not re.search(r"\bEND_PROGRAM\b", code, re.IGNORECASE):
        issues.append(Issue("error", "missing_end_program", "PROGRAM is missing END_PROGRAM."))
    if has_fb and not re.search(r"\bEND_FUNCTION_BLOCK\b", code, re.IGNORECASE):
        issues.append(
            Issue("error", "missing_end_function_block", "FUNCTION_BLOCK is missing END_FUNCTION_BLOCK.")
        )
    if has_function and not re.search(r"\bEND_FUNCTION\b", code, re.IGNORECASE):
        issues.append(Issue("error", "missing_end_function", "FUNCTION is missing END_FUNCTION."))


def _check_block_balance(lines: list[str], issues: list[Issue]) -> None:
    pairs = [
        ("IF", "END_IF"),
        ("CASE", "END_CASE"),
        ("FOR", "END_FOR"),
        ("WHILE", "END_WHILE"),
        ("REPEAT", "END_REPEAT"),
        ("VAR", "END_VAR"),
    ]

    upper_lines = [line.upper() for line in lines]
    for start, end in pairs:
        if start == "VAR":
            start_count = sum(1 for line in upper_lines if re.match(r"^\s*VAR(?:_|$|\s)", line))
        else:
            start_count = sum(len(re.findall(rf"\b{start}\b", line)) for line in upper_lines)
        end_count = sum(len(re.findall(rf"\b{end}\b", line)) for line in upper_lines)
        if start_count > end_count:
            issues.append(Issue("error", "unclosed_block", f"{start} block count exceeds {end} count."))
        elif end_count > start_count:
            issues.append(Issue("error", "extra_block_end", f"{end} appears more often than {start}."))


def _parse_declarations(code: str, issues: list[Issue]) -> tuple[dict[str, dict], set[str]]:
    declared: dict[str, dict] = {}
    declaration_types: set[str] = set()

    for match in re.finditer(r"\b(VAR(?:_[A-Z]+)?(?:\s+CONSTANT)?)\b(.*?)\bEND_VAR\b", code, re.DOTALL | re.IGNORECASE):
        direction = match.group(1).upper().replace("VAR_", "")
        block_start_line = code[: match.start()].count("\n") + 1
        block = match.group(2)

        for offset, raw_line in enumerate(block.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue

            line = line.split("//", 1)[0].strip()
            declaration = re.match(r"^([A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*)\s*:\s*([^;:=]+)", line)
            if not declaration:
                continue

            names = [name.strip() for name in declaration.group(1).split(",")]
            type_name = declaration.group(2).strip().split()[0].upper()
            declaration_types.add(type_name)

            if _looks_like_invalid_type(declaration.group(2).strip()):
                issues.append(
                    Issue(
                        "error",
                        "invalid_type",
                        f"Declaration uses non-CODESYS type '{declaration.group(2).strip()}'.",
                        block_start_line + offset,
                    )
                )

            for name in names:
                declared[name.upper()] = {
                    "name": name,
                    "type": type_name,
                    "direction": direction,
                    "line": block_start_line + offset,
                }

    if not declared:
        issues.append(Issue("error", "no_declarations", "No variables were declared in VAR blocks."))

    return declared, declaration_types


def _extract_used_identifiers(code: str, declared: dict[str, dict]) -> set[str]:
    body = re.sub(r"\bVAR(?:_[A-Z]+)?(?:\s+CONSTANT)?\b.*?\bEND_VAR\b", "\n", code, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"\b(PROGRAM|FUNCTION_BLOCK|FUNCTION)\s+\w+", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"\bEND_(PROGRAM|FUNCTION_BLOCK|FUNCTION)\b", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"'[^']*'|\"[^\"]*\"", "", body)
    body = re.sub(r"\bT#\w+\b", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\b\d+(?:\.\d+)?\b", "", body)

    identifiers = {token.upper() for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body)}
    ignored = KEYWORDS | IEC_TYPES | STANDARD_FBS | STANDARD_FUNCTIONS | STANDARD_FB_PARAMETERS | set(declared)

    # Method/property names after a dot are part of FB outputs, not standalone variables.
    dotted = {token.upper() for token in re.findall(r"\.\s*([A-Za-z_][A-Za-z0-9_]*)", body)}
    ignored |= dotted

    return {token for token in identifiers if token not in ignored}


def _check_undeclared_identifiers(
    declared: dict[str, dict],
    declaration_types: set[str],
    used: set[str],
    issues: list[Issue],
) -> None:
    custom_types = {name.upper() for name in declaration_types}
    unknown = sorted(token for token in used if token not in custom_types)

    for token in unknown[:8]:
        issues.append(Issue("error", "undeclared_identifier", f"Identifier '{token}' is used but not declared."))

    if len(unknown) > 8:
        issues.append(
            Issue(
                "warning",
                "undeclared_identifier_limit",
                f"{len(unknown) - 8} more undeclared identifiers were omitted from this report.",
            )
        )


def _check_bad_types(lines: list[str], issues: list[Issue]) -> None:
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.split("//", 1)[0]
        declaration = re.match(r"^\s*[A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*\s*:\s*([^;:=]+)", line)
        if not declaration:
            continue

        type_name = declaration.group(1).strip().split()[0]
        if _looks_like_invalid_type(type_name):
            message = INVALID_TYPE_HINTS[type_name.lower()]
            issues.append(Issue("error", "invalid_type", message, line_number))


def _check_assignment_syntax(lines: list[str], issues: list[Issue]) -> None:
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.split("//", 1)[0].strip()
        if not line or line.upper().startswith(("IF ", "ELSIF ", "WHILE ", "UNTIL ")):
            continue
        if re.match(r"^[A-Za-z_][\w.]*\s=\s[^=]", line) and "<=" not in line and ">=" not in line and "<>" not in line:
            issues.append(
                Issue("error", "assignment_operator", "Use := for assignment in Structured Text.", line_number)
            )


def _check_semicolons(lines: list[str], issues: list[Issue]) -> None:
    no_semicolon_prefixes = (
        "PROGRAM ",
        "FUNCTION_BLOCK ",
        "FUNCTION ",
        "VAR",
        "END_VAR",
        "IF ",
        "ELSIF ",
        "ELSE",
        "CASE ",
        "FOR ",
        "WHILE ",
        "REPEAT",
        "END_IF",
        "END_CASE",
        "END_FOR",
        "END_WHILE",
        "END_REPEAT",
        "END_PROGRAM",
        "END_FUNCTION_BLOCK",
        "END_FUNCTION",
    )

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.split("//", 1)[0].strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith(no_semicolon_prefixes):
            continue
        if ":" in line and re.match(r"^[A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*\s*:", line):
            continue
        if not line.endswith(";"):
            issues.append(Issue("warning", "missing_semicolon", "Statement may be missing a semicolon.", line_number))


def _check_safety_patterns(code: str, description: str, category: str, issues: list[Issue]) -> None:
    combined = f"{description} {category}".lower()
    code_lower = code.lower()
    controls_physical_output = any(
        word in combined
        for word in ("motor", "pump", "valve", "fan", "heater", "conveyor", "cylinder", "actuator", "steam")
    )

    if controls_physical_output and not any(token in code_lower for token in ("estop", "e_stop", "emergency", "safety")):
        issues.append(
            Issue(
                "warning",
                "missing_estop",
                "Physical control logic should include an emergency stop or safety interlock input.",
            )
        )

    if any(word in combined for word in ("sensor", "transmitter", "level", "temperature", "pressure", "4-20ma")):
        if not any(word in code_lower for word in ("range", "min", "max", "fault", "valid")):
            issues.append(
                Issue(
                    "warning",
                    "missing_sensor_validation",
                    "Sensor/process input logic should include range or validity checks.",
                )
            )

    if any(word in combined for word in ("motor", "pump", "valve", "actuator")):
        if not re.search(r"\b(TON|TOF|TP)\b", code, re.IGNORECASE):
            issues.append(
                Issue(
                    "info",
                    "no_timer_detected",
                    "No timer function block detected; many real devices need feedback timeout or delay logic.",
                )
            )


def _strip_comments(code: str) -> str:
    code = re.sub(r"\(\*.*?\*\)", "", code, flags=re.DOTALL)
    return re.sub(r"//.*", "", code)


def _looks_like_invalid_type(type_text: str) -> bool:
    first = type_text.split()[0]
    return first.lower() in INVALID_TYPE_HINTS and first.upper() not in IEC_TYPES


def _result(issues: list[Issue], declared: dict[str, dict], used: set[str], repaired: bool) -> dict:
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    infos = sum(1 for issue in issues if issue.severity == "info")
    score = max(0, 100 - errors * 15 - warnings * 7 - infos * 2)

    if errors:
        status = "needs_repair"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"

    return {
        "status": status,
        "score": score,
        "summary": _summary(status, errors, warnings, infos, score),
        "issues": [issue.to_dict() for issue in issues],
        "stats": {
            "declared_variables": len(declared),
            "used_external_identifiers": len(used),
            "errors": errors,
            "warnings": warnings,
            "info": infos,
        },
        "repaired": repaired,
    }


def _summary(status: str, errors: int, warnings: int, infos: int, score: int) -> str:
    if status == "passed":
        return f"Passed local ST checks with confidence score {score}."
    if status == "passed_with_warnings":
        return f"Passed core checks with {warnings} warning(s) and confidence score {score}."
    return f"Needs review: {errors} error(s), {warnings} warning(s), {infos} note(s), score {score}."
