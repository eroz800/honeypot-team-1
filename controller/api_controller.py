@app.route("/report", methods=["GET"])
def report_json():
    """
    מחליף את הפונקציה שהחזירה HTML ומחזיר JSON תקני לפרונט.
    קורא את האירועים מ-report_generator ומחזיר אותם במבנה שה-Frontend מצפה לו.
    """
    try:
        from model import report_generator
        events = report_generator.get_events_for_report()

        data = []
        for event in events:
            if isinstance(event, dict):
                # אם האירוע הוא dict עם מפתחות
                data.append({
                    "time": event.get("time", ""),
                    "trap": event.get("trap", ""),
                    "ip": event.get("ip", ""),
                    "input": event.get("input", ""),
                })
            elif isinstance(event, (list, tuple)) and len(event) >= 4:
                # אם האירוע הוא רשימה או טופל עם 4 עמודות
                data.append({
                    "time": event[0],
                    "trap": event[1],
                    "ip": event[2],
                    "input": event[3],
                })
            else:
                continue

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
