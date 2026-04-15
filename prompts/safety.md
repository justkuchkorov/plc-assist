## Safety Patterns for Industrial Control Systems

### Emergency Stop Pattern
Emergency stop (E-Stop) must ALWAYS be checked first in the scan cycle.
E-Stop is normally closed (NC) — wire breaks = safe state.

```iec
// E-Stop check — FIRST thing in every cycle
IF NOT bEStop THEN
    // Force all outputs to safe state
    bMotorRun := FALSE;
    bValveOpen := FALSE;
    // Set fault flag
    bEStopActive := TRUE;
    RETURN; // Skip all other logic
END_IF
```

### Motor Protection Pattern
- Minimum OFF time before restart (prevent thermal damage)
- Maximum consecutive starts within time window
- Overload detection with lockout (require manual reset)
- Running feedback check (if motor commanded ON but no feedback within timeout = fault)

### Interlock Patterns
- Two opposing valves: never both open simultaneously
- Sequential start: pump must be running before opening flow valve
- Level protection: stop filling when high-level reached, stop draining when low-level reached
- Pressure relief: open relief valve before pressure exceeds limit

### Alarm Handling Pattern
- Three levels: WARNING (log only), ALARM (alert operator), CRITICAL (auto-shutdown)
- Each alarm has: active flag, acknowledged flag, timestamp
- Alarms require explicit acknowledgment to clear
- Critical alarms trigger safe shutdown regardless of acknowledgment

### Sensor Validation Pattern
- Check for wire-break (value = 0 or minimum range)
- Check for short-circuit (value = maximum range)
- Rate-of-change limit (sudden jumps = sensor fault, not real process change)
- Use redundant sensors for critical measurements

### Fail-Safe Defaults
- Motors: OFF
- Valves: depends on type
  - Fail-close: de-energize = closed (most common for inlet/control valves)
  - Fail-open: de-energize = open (cooling water, relief valves)
- Heaters: OFF
- Conveyors: STOP
