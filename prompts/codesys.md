## CODESYS-Specific Syntax Rules

### Program Structure
```iec
PROGRAM ProgramName
VAR
    // Local variables
END_VAR

// Logic here

END_PROGRAM
```

### Function Block Structure
```iec
FUNCTION_BLOCK FBName
VAR_INPUT
    // Inputs
END_VAR
VAR_OUTPUT
    // Outputs
END_VAR
VAR
    // Internal variables
END_VAR

// Logic here

END_FUNCTION_BLOCK
```

### Timer Usage (CODESYS standard library)
```iec
// TON - On-delay timer
tonDelay(IN := bStartCondition, PT := T#5S);
bDelayDone := tonDelay.Q;

// TOF - Off-delay timer
tofDelay(IN := bSignal, PT := T#3S);
bDelayedOff := tofDelay.Q;

// TP - Pulse timer
tpPulse(IN := bTrigger, PT := T#1S);
bPulseActive := tpPulse.Q;
```

### Edge Detection
```iec
// Rising edge
rtrigStart(CLK := bStartButton);
IF rtrigStart.Q THEN
    // Execute once on rising edge
END_IF

// Falling edge
ftrigStop(CLK := bStopButton);
IF ftrigStop.Q THEN
    // Execute once on falling edge
END_IF
```

### CASE Statement for State Machines
```iec
CASE iState OF
    0: // IDLE
        // logic
        IF bCondition THEN
            iState := 10;
        END_IF
    10: // RUNNING
        // logic
    20: // ERROR
        // logic
END_CASE
```

### Time Literal Format
- Milliseconds: T#500MS
- Seconds: T#5S
- Minutes: T#2M
- Combined: T#1M30S
- Hours: T#1H

### Comparison and Logic Operators
- Equal: =
- Not equal: <>
- AND, OR, NOT, XOR (uppercase)
- Greater: >, >=
- Less: <, <=

### String Operations
- CONCAT(str1, str2)
- LEN(str)
- MID(str, length, position)

### Type Conversion
- BOOL_TO_INT(), INT_TO_REAL(), REAL_TO_INT()
- Always use explicit conversion, never implicit
