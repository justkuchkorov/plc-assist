## Template: Motor Start/Stop Control

Generate a motor control function block with the following structure:

### Required Elements
- FUNCTION_BLOCK with VAR_INPUT for: bStart, bStop, bEStop, bOverload, bRunFeedback (from motor contactor aux contact)
- VAR_OUTPUT for: bMotorCmd (contactor output), bRunning, bFault, iFaultCode
- Start logic: momentary start button with seal-in circuit (latch)
- Stop logic: stop button OR e-stop OR overload breaks the seal-in
- E-Stop has highest priority, checked first every scan
- Run feedback monitoring: if motor commanded ON but bRunFeedback not TRUE within timeout (e.g., T#3S) → fault
- Overload handling: if bOverload triggers, stop motor and set fault (require manual reset)
- Anti-restart: motor cannot restart after fault until fault is acknowledged AND start button is released first
- Minimum off-time: prevent rapid cycling (configurable, default T#5S)

### Fault Codes
- 0: No fault
- 1: Emergency stop activated
- 2: Overload trip
- 3: Run feedback timeout (motor didn't start)
- 4: Run feedback lost (motor stopped unexpectedly)

### Safety Considerations
- Stop and E-Stop are normally closed (NC) — wire break = safe state
- Motor contactor must have auxiliary contact wired to bRunFeedback for verification
- Overload relay is hardware — this logic only handles the software response
