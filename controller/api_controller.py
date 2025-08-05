from flask import Flask, request, jsonify, send_from_directory, render_template_string
from model.trap_manager import TrapManager
from model.ssh_trap import SshTrap

app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return "Honeypot is live"

# Init manager
manager = TrapManager()
manager.add_trap(SshTrap())

# Simulation endpoint
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    trap_type = data.get("trap_type")
    input_data = data.get("input")
    ip = data.get("ip")

    if not all([trap_type, input_data, ip]):
        return jsonify({"error": "Missing parameters"}), 400

    result = manager.run_trap(trap_type, input_data, ip)
    return jsonify({"status": result}), 200

# Dashboard HTML
@app.route("/dashboard")
def dashboard():
    with open("view/dashboard.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

@app.route("/summary")
def summary():
    with open("reports/summary.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())
 
# CSS file serving
@app.route("/style.css")
def serve_css():
    return send_from_directory("view", "style.css")

# Run app
if __name__ == "__main__":
    app.run(debug=True)
