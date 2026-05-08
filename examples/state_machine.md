# Few-Shot Examples: State Machines

These examples are original PLC Assist patterns. Use them to learn safe state transitions, timeout handling, and readable CODESYS state-machine structure.

## Example 1: Bottle Filling Station

Requirement:
Bottle station sequence with IDLE, FILL, CAP, EJECT, and FAULT states. Emergency stop must force safe outputs. Each motion/fill step has a timeout and reset returns to IDLE only when E-stop is healthy.

Expected pattern:
```iec
FUNCTION_BLOCK BottleFillingStation
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

END_FUNCTION_BLOCK
```

Quality notes:
- Outputs default to safe values before the CASE block.
- Timer FBs are called with named parameters; code does not assign `tonTimer.PT` or `tonTimer.IN`.
- Each timeout has an explicit fault code.
- Reset is edge-triggered and only works when E-stop is healthy.

