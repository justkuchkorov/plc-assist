import unittest
from pathlib import Path

from validator import validate_st_code


VALID_MOTOR_CODE = """
FUNCTION_BLOCK MotorControl
VAR_INPUT
    bEStop : BOOL;
    bStart : BOOL;
    bStop : BOOL;
    bOverload : BOOL;
END_VAR
VAR_OUTPUT
    bMotorRun : BOOL;
    bFault : BOOL;
END_VAR
VAR
    tonFeedback : TON;
END_VAR

IF NOT bEStop THEN
    bMotorRun := FALSE;
    bFault := TRUE;
    RETURN;
END_IF

tonFeedback(IN := bMotorRun, PT := T#5S);

IF bOverload THEN
    bMotorRun := FALSE;
    bFault := TRUE;
ELSIF bStop THEN
    bMotorRun := FALSE;
ELSIF bStart AND NOT bFault THEN
    bMotorRun := TRUE;
END_IF

END_FUNCTION_BLOCK
"""


class ValidatorTests(unittest.TestCase):
    def test_valid_motor_code_passes_core_checks(self):
        result = validate_st_code(
            VALID_MOTOR_CODE,
            "Pump motor with emergency stop, overload, and feedback timeout.",
            "motor_control",
        )

        self.assertNotEqual(result["status"], "needs_repair")
        self.assertEqual(result["stats"]["errors"], 0)
        self.assertGreaterEqual(result["score"], 90)

    def test_undeclared_variable_is_error(self):
        code = """
PROGRAM MainProgram
VAR
    bStart : BOOL;
END_VAR

bMotorRun := bStart;

END_PROGRAM
"""

        result = validate_st_code(code, "Motor starter", "motor_control")
        issue_codes = {issue["code"] for issue in result["issues"]}

        self.assertEqual(result["status"], "needs_repair")
        self.assertIn("undeclared_identifier", issue_codes)

    def test_invalid_lowercase_type_is_error(self):
        code = """
PROGRAM MainProgram
VAR
    rTemperature : float;
END_VAR

rTemperature := 20.0;

END_PROGRAM
"""

        result = validate_st_code(code, "Temperature monitor", "general")
        issue_codes = {issue["code"] for issue in result["issues"]}

        self.assertEqual(result["status"], "needs_repair")
        self.assertIn("invalid_type", issue_codes)

    def test_curated_examples_pass_core_checks(self):
        examples_dir = Path(__file__).parent / "examples"

        for path in examples_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            code_blocks = []
            for block in text.split("```iec")[1:]:
                code_blocks.append(block.split("```", 1)[0].strip())

            self.assertGreater(len(code_blocks), 0, f"{path.name} should include IEC examples")

            for code in code_blocks:
                result = validate_st_code(code, path.stem, path.stem)
                self.assertEqual(
                    result["stats"]["errors"],
                    0,
                    f"{path.name} example has validation errors: {result['issues']}",
                )


if __name__ == "__main__":
    unittest.main()
