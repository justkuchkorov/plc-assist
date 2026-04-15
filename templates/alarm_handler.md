## Template: Alarm Handling

Generate an alarm handler with the following structure:

### Required Elements
- FUNCTION_BLOCK for individual alarm with VAR_INPUT: bCondition, bAcknowledge, bReset
- VAR_OUTPUT for: bActive, bAcknowledged, bLatched, iSeverity (1=Warning, 2=Alarm, 3=Critical)
- Alarm becomes active when bCondition is TRUE
- Alarm latches — stays active even if condition clears (until acknowledged + reset)
- Acknowledgment only marks it as seen, does NOT clear the alarm
- Reset clears the alarm ONLY if the condition is no longer active
- Critical alarms (severity 3) trigger an output flag for emergency shutdown

### Safety Considerations
- Alarms must never auto-clear without operator acknowledgment
- Critical alarms should trigger safe shutdown via separate logic
- Alarm state should survive PLC warm restart (use RETAIN variables)
