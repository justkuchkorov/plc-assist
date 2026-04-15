## Template: State Machine

Generate a state machine with the following structure:

### Required Elements
- PROGRAM or FUNCTION_BLOCK with iState (INT) variable
- CASE statement with numbered states (use multiples of 10 for easy insertion: 0, 10, 20, 30...)
- State 0 is always IDLE
- Last state is always ERROR/FAULT
- Each state has:
  - Entry action (execute once on state entry, use a bStateEntry flag)
  - Continuous action (execute every scan while in this state)
  - Transition conditions (what moves to the next state)
  - Timeout (if stuck in a state too long → fault)
- Global E-Stop check BEFORE the CASE statement (forces state to ERROR from anywhere)
- Error state requires explicit reset command to return to IDLE
- State transition logging: store previous state for debugging

### Safety Considerations
- All outputs must have defined values in EVERY state (no floating outputs)
- ERROR state must force all outputs to safe values
- Timeouts on every state that involves waiting for physical process
- Never skip states — always transition through intermediate states
