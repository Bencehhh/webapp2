@app.route("/chatbox", methods=["POST"])
def chatbox_command():
    global LICENSE_KEY  # Move this to the top of the function
    command = request.form.get("command", "").strip().lower()
    response_message = ""

    if command == "/balance":
        if not LICENSE_KEY:
            response_message = "License key is required. Please set it first."
        else:
            url = f"{BASE_URL}/check_balance?license_key={LICENSE_KEY}"
            result = debug_request(url)
            response_message = f"Balance Info: {result}" if result else "Failed to check balance."

    elif command.startswith("/email_lookup"):
        if not LICENSE_KEY:
            response_message = "License key is required. Please set it first."
        else:
            parts = command.split()
            if len(parts) != 2:
                response_message = "Usage: /email_lookup <email>"
            else:
                email = parts[1]
                url = f"{BASE_URL}/email_lookup?email={email}&license_key={LICENSE_KEY}"
                result = debug_request(url)
                response_message = f"Email Lookup Result for {email}: {result}" if result else "Failed to perform email lookup."

    elif command.startswith("/ssn_lookup"):
        if not LICENSE_KEY:
            response_message = "License key is required. Please set it first."
        else:
            parts = command.split()
            if len(parts) != 4:
                response_message = "Usage: /ssn_lookup <first_name> <last_name> <dob>"
            else:
                fname, lname, dob = parts[1], parts[2], parts[3]
                url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={LICENSE_KEY}"
                result = debug_request(url)
                response_message = f"SSN Lookup Result for {fname} {lname} (DOB: {dob}): {result}" if result else "Failed to perform SSN lookup."

    elif command.startswith("/set_license"):
        parts = command.split()
        if len(parts) != 2:
            response_message = "Usage: /set_license <license_key>"
        else:
            LICENSE_KEY = parts[1]
            response_message = f"License key has been updated to: {LICENSE_KEY}"

    else:
        response_message = "Unknown command. Available commands: /balance, /email_lookup, /ssn_lookup, /set_license"

    send_to_discord("Chatbox Command Response", response_message)
    return jsonify({"message": response_message})
