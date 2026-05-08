from validator import validate_st_code


def infer_category(description: str, category: str) -> str:
    if category and category != "general":
        return category

    text = description.lower()
    if any(word in text for word in ("pid", "setpoint", "temperature", "cooling", "analog", "4-20ma")):
        return "pid_loop"
    if any(word in text for word in ("valve", "solenoid", "open", "close", "limit switch")):
        return "valve_control"
    if any(word in text for word in ("motor", "pump", "fan", "conveyor", "overload")):
        return "motor_control"
    if any(word in text for word in ("state", "sequence", "station", "idle")):
        return "state_machine"
    if any(word in text for word in ("alarm", "warning", "critical", "acknowledge")):
        return "alarm_handler"
    return category or "general"


def build_fallback_result(description: str, category: str, reason: str = "") -> dict:
    effective_category = infer_category(description, category)

    if effective_category == "pid_loop":
        result = _pid_transformer_fallback()
    elif effective_category == "motor_control":
        result = _motor_fallback()
    elif effective_category == "state_machine":
        result = _state_machine_fallback()
    elif effective_category == "valve_control":
        result = _valve_fallback()
    else:
        result = _general_fallback()

    result["fallback"] = True
    result["fallback_reason"] = reason or "Model unavailable; returned local validated pattern."
    result["effective_category"] = effective_category
    result["validation"] = validate_st_code(result["code"], description, effective_category)
    result["warnings"] = (
        f"- Local fallback used because the model was unavailable.\n"
        f"- {result['warnings']}"
    )
    return result


def _pid_transformer_fallback() -> dict:
    code = """FUNCTION_BLOCK TransformerCoolingPID
VAR_INPUT
    bEnable : BOOL;
    bEStopOk : BOOL;
    bReset : BOOL;
    bTempSensorValid : BOOL;
    rTransformerTemp : REAL;
    rSetpointTemp : REAL := 75.0;
    rKp : REAL := 2.0;
    rKi : REAL := 0.1;
    rKd : REAL := 0.0;
END_VAR
VAR_OUTPUT
    rFanSpeedPercent : REAL;
    bFanStage1 : BOOL;
    bFanStage2 : BOOL;
    bFanStage3 : BOOL;
    bActive : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
END_VAR
VAR
    rError : REAL;
    rIntegral : REAL;
    rDerivative : REAL;
    rPreviousTemp : REAL;
    rRawOutput : REAL;
END_VAR

IF NOT bEStopOk THEN
    rFanSpeedPercent := 0.0;
    bFanStage1 := FALSE;
    bFanStage2 := FALSE;
    bFanStage3 := FALSE;
    bActive := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
    RETURN;
END_IF

IF bReset THEN
    rIntegral := 0.0;
    rPreviousTemp := rTransformerTemp;
    bFault := FALSE;
    iFaultCode := 0;
END_IF

IF NOT bEnable THEN
    rFanSpeedPercent := 0.0;
    bFanStage1 := FALSE;
    bFanStage2 := FALSE;
    bFanStage3 := FALSE;
    bActive := FALSE;
    RETURN;
END_IF

IF NOT bTempSensorValid OR (rTransformerTemp < -20.0) OR (rTransformerTemp > 160.0) THEN
    rFanSpeedPercent := 100.0;
    bFanStage1 := TRUE;
    bFanStage2 := TRUE;
    bFanStage3 := TRUE;
    bFault := TRUE;
    iFaultCode := 2;
    RETURN;
END_IF

rError := rTransformerTemp - rSetpointTemp;
rIntegral := rIntegral + (rError * rKi);
rDerivative := (rTransformerTemp - rPreviousTemp) * rKd;
rRawOutput := (rError * rKp) + rIntegral + rDerivative;

IF rRawOutput > 100.0 THEN
    rFanSpeedPercent := 100.0;
    rIntegral := rIntegral - (rError * rKi);
ELSIF rRawOutput < 0.0 THEN
    rFanSpeedPercent := 0.0;
    rIntegral := rIntegral - (rError * rKi);
ELSE
    rFanSpeedPercent := rRawOutput;
END_IF

bFanStage1 := rFanSpeedPercent >= 20.0;
bFanStage2 := rFanSpeedPercent >= 50.0;
bFanStage3 := rFanSpeedPercent >= 80.0;
bActive := TRUE;
rPreviousTemp := rTransformerTemp;

END_FUNCTION_BLOCK"""

    return {
        "code": code,
        "variables": """| Name | Type | Direction | Description |
|------|------|-----------|-------------|
| bEnable | BOOL | Input | Enables automatic cooling control |
| bEStopOk | BOOL | Input | Emergency stop healthy signal |
| bTempSensorValid | BOOL | Input | Temperature sensor validity flag |
| rTransformerTemp | REAL | Input | Current transformer temperature |
| rSetpointTemp | REAL | Input | Target transformer temperature |
| rFanSpeedPercent | REAL | Output | Requested cooling fan speed |
| bFanStage1..3 | BOOL | Output | Fan stage commands |
| bFault | BOOL | Output | Fault active flag |
| iFaultCode | INT | Output | 0 none, 1 E-stop, 2 sensor fault |""",
        "explanation": """1. Emergency stop is checked first and immediately forces all fans off.
2. Reset clears PID memory and existing faults.
3. Disabled mode sets the cooling output to zero.
4. Sensor fault drives fans to full speed as a conservative transformer-protection fallback.
5. PID output is clamped between 0 and 100 percent.
6. Fan stages turn on at 20, 50, and 80 percent output.""",
        "warnings": "Verify whether emergency stop should remove fan power or whether transformer cooling requires a separate safety philosophy.",
        "raw": "",
        "repaired": False,
    }


def _motor_fallback() -> dict:
    code = """FUNCTION_BLOCK SafeMotorStarter
VAR_INPUT
    bStart : BOOL;
    bStop : BOOL;
    bEStopOk : BOOL;
    bOverloadOk : BOOL;
    bRunFeedback : BOOL;
    bReset : BOOL;
END_VAR
VAR_OUTPUT
    bMotorCmd : BOOL;
    bRunning : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
END_VAR
VAR
    bLatched : BOOL;
    tonFeedback : TON;
END_VAR

IF NOT bEStopOk THEN
    bMotorCmd := FALSE;
    bLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
    RETURN;
END_IF

IF NOT bOverloadOk THEN
    bMotorCmd := FALSE;
    bLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 2;
END_IF

IF bReset AND bEStopOk AND bOverloadOk AND NOT bStart THEN
    bFault := FALSE;
    iFaultCode := 0;
END_IF

IF bStop OR bFault THEN
    bLatched := FALSE;
ELSIF bStart AND NOT bFault THEN
    bLatched := TRUE;
END_IF

bMotorCmd := bLatched AND NOT bFault;
tonFeedback(IN := bMotorCmd AND NOT bRunFeedback, PT := T#3S);

IF tonFeedback.Q THEN
    bMotorCmd := FALSE;
    bLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 3;
END_IF

bRunning := bMotorCmd AND bRunFeedback;

END_FUNCTION_BLOCK"""
    return {
        "code": code,
        "variables": "| Name | Type | Direction | Description |\n|------|------|-----------|-------------|\n| bStart/bStop | BOOL | Input | Operator commands |\n| bEStopOk | BOOL | Input | Emergency stop healthy signal |\n| bOverloadOk | BOOL | Input | Overload relay healthy signal |\n| bMotorCmd | BOOL | Output | Motor contactor command |\n| bFault | BOOL | Output | Fault active flag |",
        "explanation": "1. E-stop has first priority.\n2. Overload trips latch a fault.\n3. Reset requires start released.\n4. Feedback timer detects commanded motor with no run feedback.",
        "warnings": "Overload and emergency stop must also be handled in hardware safety circuits.",
        "raw": "",
        "repaired": False,
    }


def _valve_fallback() -> dict:
    code = """FUNCTION_BLOCK SimpleValveControl
VAR_INPUT
    bOpenCmd : BOOL;
    bCloseCmd : BOOL;
    bEStopOk : BOOL;
    bOpenFeedback : BOOL;
    bClosedFeedback : BOOL;
    bReset : BOOL;
END_VAR
VAR_OUTPUT
    bOpenOutput : BOOL;
    bCloseOutput : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
END_VAR
VAR
    tonTravel : TON;
END_VAR

IF NOT bEStopOk THEN
    bOpenOutput := FALSE;
    bCloseOutput := FALSE;
    bFault := TRUE;
    iFaultCode := 5;
    RETURN;
END_IF

IF bOpenFeedback AND bClosedFeedback THEN
    bOpenOutput := FALSE;
    bCloseOutput := FALSE;
    bFault := TRUE;
    iFaultCode := 3;
END_IF

IF bReset THEN
    bFault := FALSE;
    iFaultCode := 0;
END_IF

bOpenOutput := bOpenCmd AND NOT bCloseCmd AND NOT bFault AND NOT bOpenFeedback;
bCloseOutput := bCloseCmd AND NOT bOpenCmd AND NOT bFault AND NOT bClosedFeedback;
tonTravel(IN := bOpenOutput OR bCloseOutput, PT := T#30S);

IF tonTravel.Q THEN
    bOpenOutput := FALSE;
    bCloseOutput := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
END_IF

END_FUNCTION_BLOCK"""
    return {
        "code": code,
        "variables": "| Name | Type | Direction | Description |\n|------|------|-----------|-------------|\n| bOpenCmd/bCloseCmd | BOOL | Input | Valve movement commands |\n| bEStopOk | BOOL | Input | Emergency stop healthy signal |\n| bOpenOutput/bCloseOutput | BOOL | Output | Solenoid commands |\n| bFault | BOOL | Output | Fault active flag |",
        "explanation": "1. E-stop de-energizes both solenoids.\n2. Both limit switches active creates a sensor fault.\n3. Open and close outputs are mutually exclusive.\n4. Travel timeout creates a fault.",
        "warnings": "Confirm the valve fail-safe position and travel timeout with the real actuator datasheet.",
        "raw": "",
        "repaired": False,
    }


def _state_machine_fallback() -> dict:
    code = """FUNCTION_BLOCK BottleFillingStation
VAR_INPUT
    bStart : BOOL;
    bReset : BOOL;
    bEStopOk : BOOL;
    bBottlePresent : BOOL;
    bLevelReached : BOOL;
    bCapDone : BOOL;
    bEjectDone : BOOL;
END_VAR
VAR_OUTPUT
    bFillValve : BOOL;
    bCapCylinder : BOOL;
    bEjectCylinder : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
    iState : INT;
END_VAR
VAR
    rtrigStart : R_TRIG;
    rtrigReset : R_TRIG;
    tonFill : TON;
    tonCap : TON;
    tonEject : TON;
END_VAR

IF NOT bEStopOk THEN
    bFillValve := FALSE;
    bCapCylinder := FALSE;
    bEjectCylinder := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
    iState := 900;
    RETURN;
END_IF

rtrigReset(CLK := bReset);
IF rtrigReset.Q AND bEStopOk THEN
    bFault := FALSE;
    iFaultCode := 0;
    iState := 0;
END_IF

bFillValve := FALSE;
bCapCylinder := FALSE;
bEjectCylinder := FALSE;

rtrigStart(CLK := bStart);
tonFill(IN := iState = 10, PT := T#10S);
tonCap(IN := iState = 20, PT := T#3S);
tonEject(IN := iState = 30, PT := T#3S);

CASE iState OF
    0:
        IF rtrigStart.Q AND bBottlePresent AND NOT bFault THEN
            iState := 10;
        END_IF

    10:
        bFillValve := TRUE;
        IF bLevelReached THEN
            iState := 20;
        ELSIF tonFill.Q THEN
            bFault := TRUE;
            iFaultCode := 2;
            iState := 900;
        END_IF

    20:
        bCapCylinder := TRUE;
        IF bCapDone THEN
            iState := 30;
        ELSIF tonCap.Q THEN
            bFault := TRUE;
            iFaultCode := 3;
            iState := 900;
        END_IF

    30:
        bEjectCylinder := TRUE;
        IF bEjectDone THEN
            iState := 0;
        ELSIF tonEject.Q THEN
            bFault := TRUE;
            iFaultCode := 4;
            iState := 900;
        END_IF

    900:
        bFillValve := FALSE;
        bCapCylinder := FALSE;
        bEjectCylinder := FALSE;
        bFault := TRUE;
END_CASE

END_FUNCTION_BLOCK"""
    return {
        "code": code,
        "variables": "| Name | Type | Direction | Description |\n|------|------|-----------|-------------|\n| bStart/bReset | BOOL | Input | Operator commands |\n| bEStopOk | BOOL | Input | Emergency stop healthy signal |\n| bBottlePresent | BOOL | Input | Bottle present sensor |\n| bLevelReached | BOOL | Input | Fill level reached sensor |\n| bFillValve | BOOL | Output | Fill valve command |\n| bCapCylinder | BOOL | Output | Capping cylinder command |\n| bEjectCylinder | BOOL | Output | Eject cylinder command |\n| bFault | BOOL | Output | Fault active flag |\n| iFaultCode | INT | Output | 1 E-stop, 2 fill timeout, 3 cap timeout, 4 eject timeout |",
        "explanation": "1. Emergency stop forces all outputs safe and enters fault state.\n2. Outputs default to safe values before the CASE block.\n3. Each active state has its own timer function block.\n4. Timeout faults move the sequence to state 900.\n5. Reset clears faults only when E-stop is healthy.",
        "warnings": "Add real feedback sensors for cap/eject extend and retract positions before using on hardware.",
        "raw": "",
        "repaired": False,
    }


def _general_fallback() -> dict:
    code = """PROGRAM MainProgram
VAR
    bEnable : BOOL;
    bEStopOk : BOOL;
    bOutputCmd : BOOL;
    bFault : BOOL;
END_VAR

IF NOT bEStopOk THEN
    bOutputCmd := FALSE;
    bFault := TRUE;
    RETURN;
END_IF

bOutputCmd := bEnable AND NOT bFault;

END_PROGRAM"""
    return {
        "code": code,
        "variables": "| Name | Type | Direction | Description |\n|------|------|-----------|-------------|\n| bEnable | BOOL | Local | Enable condition |\n| bEStopOk | BOOL | Local | Emergency stop healthy signal |\n| bOutputCmd | BOOL | Local | Safe output command |\n| bFault | BOOL | Local | Fault active flag |",
        "explanation": "1. E-stop is checked first.\n2. Output is only enabled when no fault is active.",
        "warnings": "This is a generic fallback. Add real I/O names, reset behavior, and device-specific interlocks before use.",
        "raw": "",
        "repaired": False,
    }
