# Few-Shot Examples: PID Loop

These examples are original PLC Assist patterns. Use them to learn CODESYS-safe declarations, range checks, clamping, and deterministic scan behavior.

## Example 1: Analog Cooling Valve Controller

Requirement:
Control a cooling valve from 0 to 100 percent using process temperature, setpoint, PID gains, enable/reset, sensor valid flag, and sample time.

Expected pattern:
```iec
FUNCTION_BLOCK CoolingValvePID
VAR_INPUT
    bEnable : BOOL;
    bReset : BOOL;
    bSensorValid : BOOL;
    rSetpoint : REAL;
    rProcessValue : REAL;
    rKp : REAL;
    rKi : REAL;
    rKd : REAL;
    tSampleTime : TIME := T#500MS;
END_VAR
VAR_OUTPUT
    rOutputPercent : REAL;
    bActive : BOOL;
    bLimited : BOOL;
    bFault : BOOL;
END_VAR
VAR
    rError : REAL;
    rPreviousProcessValue : REAL;
    rIntegral : REAL;
    rDerivative : REAL;
    rRawOutput : REAL;
    tonSample : TON;
END_VAR

IF bReset OR NOT bEnable THEN
    rOutputPercent := 0.0;
    rIntegral := 0.0;
    rPreviousProcessValue := rProcessValue;
    bActive := FALSE;
    bLimited := FALSE;
    bFault := FALSE;
    RETURN;
END_IF

IF NOT bSensorValid OR (rSetpoint < 0.0) OR (rSetpoint > 150.0) THEN
    rOutputPercent := 0.0;
    bActive := FALSE;
    bFault := TRUE;
    RETURN;
END_IF

tonSample(IN := TRUE, PT := tSampleTime);

IF tonSample.Q THEN
    tonSample(IN := FALSE, PT := tSampleTime);

    rError := rSetpoint - rProcessValue;
    rIntegral := rIntegral + (rError * rKi);
    rDerivative := (rPreviousProcessValue - rProcessValue) * rKd;
    rRawOutput := (rError * rKp) + rIntegral + rDerivative;

    IF rRawOutput > 100.0 THEN
        rOutputPercent := 100.0;
        rIntegral := rIntegral - (rError * rKi);
        bLimited := TRUE;
    ELSIF rRawOutput < 0.0 THEN
        rOutputPercent := 0.0;
        rIntegral := rIntegral - (rError * rKi);
        bLimited := TRUE;
    ELSE
        rOutputPercent := rRawOutput;
        bLimited := FALSE;
    END_IF

    rPreviousProcessValue := rProcessValue;
END_IF

bActive := TRUE;

END_FUNCTION_BLOCK
```

Quality notes:
- Disable/reset forces output to safe zero.
- Sensor validity is checked before control action.
- Derivative is based on process value to reduce derivative kick.
- Output is clamped and integral is backed out during saturation.

