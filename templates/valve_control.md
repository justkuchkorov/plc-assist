## Template: Valve Control with Feedback

Generate a valve control function block with the following structure:

### Required Elements
- FUNCTION_BLOCK with VAR_INPUT for: bOpenCmd, bCloseCmd, bEStop, bOpenFeedback (limit switch), bClosedFeedback (limit switch)
- VAR_OUTPUT for: bOpenOutput (solenoid), bCloseOutput (solenoid), bIsOpen, bIsClosed, bInTransit, bFault, iFaultCode
- Open command: energize open solenoid, de-energize close solenoid
- Close command: energize close solenoid, de-energize open solenoid
- Never energize both solenoids simultaneously (interlock)
- Transit monitoring: if valve commanded open but bOpenFeedback not TRUE within travel time → fault
- Stuck detection: if both feedback switches active simultaneously → fault (broken sensor)
- E-Stop: de-energize both solenoids (valve goes to fail-safe position)

### Fault Codes
- 0: No fault
- 1: Open travel timeout
- 2: Close travel timeout
- 3: Both limit switches active (sensor fault)
- 4: Neither limit switch active when not in transit (position unknown)
- 5: Emergency stop

### Safety Considerations
- Valve fail-safe position depends on application (configure as parameter)
- Travel time timeout should be configurable (valves vary from 2s to 60s+)
- After E-Stop, require manual reset before accepting new commands
