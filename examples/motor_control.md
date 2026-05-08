# Few-Shot Examples: Motor Control

These examples are original PLC Assist patterns. Use them to learn structure, naming, declarations, timer usage, and safety behavior.

## Example 1: Pump With E-Stop, Overload, Feedback Timeout

Requirement:
Pump motor start/stop with NC emergency stop, NC overload relay, contactor feedback, 3 second start feedback timeout, and manual reset after fault.

Expected pattern:
```iec
FUNCTION_BLOCK PumpMotorControl
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
    bStartLatched : BOOL;
    bStartReleased : BOOL := TRUE;
    tonFeedback : TON;
END_VAR

IF NOT bEStopOk THEN
    bMotorCmd := FALSE;
    bStartLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 1;
    RETURN;
END_IF

IF NOT bOverloadOk THEN
    bMotorCmd := FALSE;
    bStartLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 2;
END_IF

IF NOT bStart THEN
    bStartReleased := TRUE;
END_IF

IF bReset AND bStartReleased AND bEStopOk AND bOverloadOk THEN
    bFault := FALSE;
    iFaultCode := 0;
END_IF

IF bStop OR bFault THEN
    bStartLatched := FALSE;
ELSIF bStart AND bStartReleased AND NOT bFault THEN
    bStartLatched := TRUE;
    bStartReleased := FALSE;
END_IF

bMotorCmd := bStartLatched AND NOT bFault;
tonFeedback(IN := bMotorCmd AND NOT bRunFeedback, PT := T#3S);

IF tonFeedback.Q THEN
    bMotorCmd := FALSE;
    bStartLatched := FALSE;
    bFault := TRUE;
    iFaultCode := 3;
END_IF

bRunning := bMotorCmd AND bRunFeedback;

END_FUNCTION_BLOCK
```

Quality notes:
- E-stop is checked first and returns immediately.
- Fault reset requires start button release to prevent surprise restart.
- Timer instance is declared and called with named parameters.
- Outputs are forced safe on faults.

