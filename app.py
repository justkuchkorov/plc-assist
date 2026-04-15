from flask import Flask, render_template, request, jsonify
from generator import generate_st_code

app = Flask(__name__)

CATEGORIES = [
    {"id": "general", "name": "General / Custom", "icon": "settings"},
    {"id": "pid_loop", "name": "PID Control Loop", "icon": "show_chart"},
    {"id": "motor_control", "name": "Motor Control", "icon": "electric_bolt"},
    {"id": "state_machine", "name": "State Machine", "icon": "account_tree"},
    {"id": "alarm_handler", "name": "Alarm Handling", "icon": "notifications_active"},
    {"id": "valve_control", "name": "Valve Control", "icon": "valve"},
]

EXAMPLES = {
    "pid_loop": "PID controller for tank water level. Setpoint 75%, 4-20mA level transmitter input, control output to proportional valve CV-101. Alarm at 90% high and 10% low.",
    "motor_control": "Pump motor start/stop with overload protection, emergency stop, 3 retry attempts before lockout, and run feedback monitoring.",
    "state_machine": "Bottle filling station: IDLE → FILL (open valve until level sensor) → CAP (activate capping cylinder) → EJECT (push to conveyor) → back to IDLE. Emergency stop at any point.",
    "alarm_handler": "Temperature alarm system for a furnace. Warning at 450C, alarm at 500C, critical shutdown at 550C. Each alarm must be acknowledged by operator.",
    "valve_control": "Motorized ball valve for steam header isolation. 30 second travel time, open and closed limit switches, fail-close on emergency stop.",
}


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, examples=EXAMPLES)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    description = data.get("description", "").strip()
    category = data.get("category", "general")

    if not description:
        return jsonify({"error": "Please enter a description."}), 400

    result = generate_st_code(description, category)

    if "error" in result and result["error"]:
        return jsonify(result), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, port=5001)
