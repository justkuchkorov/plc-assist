## Template: PID Control Loop

Generate a PID controller with the following structure:

### Required Elements
- FUNCTION_BLOCK with VAR_INPUT for: rSetpoint, rProcessValue, rKp, rKi, rKd, tSampleTime, bEnable, bReset
- VAR_OUTPUT for: rOutput (0.0 to 100.0%), bActive, bLimited
- Internal variables for: rError, rErrorPrev, rIntegral, rDerivative, rProportional
- Anti-windup: clamp integral term when output is saturated
- Derivative kick prevention: calculate derivative on process value, not error
- Output clamping: configurable MIN/MAX limits (default 0.0 to 100.0)
- Bumpless transfer: when switching from manual to auto, initialize integral to match current output
- Sample time enforcement: only calculate when sample timer expires

### Safety Considerations
- If bEnable goes FALSE, set output to 0.0 and reset integral
- If bReset is TRUE, clear all accumulated terms
- Check for valid setpoint range
- Rate limit the output change per scan (prevent sudden jumps)
