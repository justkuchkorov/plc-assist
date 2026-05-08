# Few-Shot Examples: Valve Control

These examples are original PLC Assist patterns. Use them to learn interlocks, feedback timeout handling, and fail-safe output behavior.

## Example 1: Motorized Isolation Valve

Requirement:
Open/close motorized valve with open and closed limit switches, emergency stop, 30 second travel timeout, reset after fault, and never energize both outputs.

Expected pattern:
```iec
FUNCTION_BLOCK MotorizedValveControl
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
    bIsOpen : BOOL;
    bIsClosed : BOOL;
    bInTransit : BOOL;
    bFault : BOOL;
    iFaultCode : INT;
END_VAR
VAR
    bCommandOpen : BOOL;
    bCommandClose : BOOL;
    tonTravel : TON;
END_VAR

IF NOT bEStopOk THEN
    bOpenOutput := FALSE;
    bCloseOutput := FALSE;
    bCommandOpen := FALSE;
    bCommandClose := FALSE;
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

IF bReset AND bEStopOk AND NOT (bOpenFeedback AND bClosedFeedback) THEN
    bFault := FALSE;
    iFaultCode := 0;
END_IF

IF NOT bFault THEN
    IF bOpenCmd AND NOT bCloseCmd AND NOT bOpenFeedback THEN
        bCommandOpen := TRUE;
        bCommandClose := FALSE;
    ELSIF bCloseCmd AND NOT bOpenCmd AND NOT bClosedFeedback THEN
        bCommandOpen := FALSE;
        bCommandClose := TRUE;
    ELSIF bOpenFeedback OR bClosedFeedback THEN
        bCommandOpen := FALSE;
        bCommandClose := FALSE;
    END_IF
END_IF

bOpenOutput := bCommandOpen AND NOT bCommandClose AND NOT bFault;
bCloseOutput := bCommandClose AND NOT bCommandOpen AND NOT bFault;
bInTransit := bOpenOutput OR bCloseOutput;

tonTravel(IN := bInTransit, PT := T#30S);

IF tonTravel.Q THEN
    bOpenOutput := FALSE;
    bCloseOutput := FALSE;
    bCommandOpen := FALSE;
    bCommandClose := FALSE;
    bFault := TRUE;
    IF bOpenCmd THEN
        iFaultCode := 1;
    ELSE
        iFaultCode := 2;
    END_IF
END_IF

bIsOpen := bOpenFeedback AND NOT bClosedFeedback;
bIsClosed := bClosedFeedback AND NOT bOpenFeedback;

END_FUNCTION_BLOCK
```

Quality notes:
- E-stop de-energizes both outputs and returns immediately.
- Open/close outputs are mutually exclusive.
- Both limit switches active is treated as a sensor fault.
- Travel timer watches movement and creates a fault on timeout.

