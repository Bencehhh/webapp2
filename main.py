import os
import requests
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from time import sleep

# Load environment variables
load_dotenv()

# Override base URL with the provided IP address
BASE_URL = "http://205.185.117.225:9203"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise EnvironmentError("DISCORD_WEBHOOK_URL is not set. Please add it to your environment variables.")

app = Flask(__name__)

# Store license key in memory for dynamic updates
LICENSE_KEY = ""

def debug_request(endpoint, retries=3):
    """ Helper to send requests with retries and detailed debugging info """
    for attempt in range(retries):
        try:
            print(f"Requesting URL: {endpoint} (Attempt {attempt + 1}/{retries})")
            response = requests.get(endpoint, timeout=20)  # Increased timeout to 20 seconds
            print("Response Status Code:", response.status_code)
            print("Response Content:", response.text)

            if response.ok:
                return response.json()
            else:
                print("Error:", response.text)
                return None
        except requests.exceptions.ReadTimeout:
            print("The request timed out. Retrying...")
        except requests.exceptions.RequestException as e:
            print("Request error:", e)
        sleep(2)  # Wait before retrying

    return {"error": "The request failed after multiple attempts."}

def send_to_discord(title, description, color=3447003):
    """ Sends an embed to the Discord webhook """
    embed = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
            }
        ]
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed)
        if response.ok:
            print("Notification sent to Discord.")
        else:
            print("Failed to send Discord notification:", response.text)
    except requests.exceptions.RequestException as e:
        print("Error sending to Discord:", e)

# Existing routes
@app.route("/check_balance", methods=["GET"])
def check_balance():
    if not LICENSE_KEY:
        return jsonify({"error": "License key is required. Please set it first."}), 400

    url = f"{BASE_URL}/check_balance?license_key={LICENSE_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord("Balance Check", f"Balance Info: {result}")
    return jsonify(result or {"error": "Failed to check balance"})

@app.route("/email_lookup", methods=["GET"])
def email_lookup():
    if not LICENSE_KEY:
        return jsonify({"error": "License key is required. Please set it first."}), 400

    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    url = f"{BASE_URL}/email_lookup?email={email}&license_key={LICENSE_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord("Email Lookup", f"Email Lookup Result for {email}: {result}")
    return jsonify(result or {"error": "Failed to perform email lookup"})

@app.route("/ssn_lookup", methods=["GET"])
def ssn_lookup():
    if not LICENSE_KEY:
        return jsonify({"error": "License key is required. Please set it first."}), 400

    fname = request.args.get("fname")
    lname = request.args.get("lname")
    dob = request.args.get("dob")
    if not all([fname, lname, dob]):
        return jsonify({"error": "First name, last name, and DOB are required"}), 400
    url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={LICENSE_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord("SSN Lookup", f"SSN Lookup Result for {fname} {lname} (DOB: {dob}): {result}")
    return jsonify(result or {"error": "Failed to perform SSN lookup"})

# New route for chatbox commands
@app.route("/chatbox", methods=["POST"])
def chatbox_command():
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
            global LICENSE_KEY
            LICENSE_KEY = parts[1]
            response_message = f"License key has been updated to: {LICENSE_KEY}"

    else:
        response_message = "Unknown command. Available commands: /balance, /email_lookup, /ssn_lookup, /set_license"

    send_to_discord("Chatbox Command Response", response_message)
    return jsonify({"message": response_message})

# Chatbox front-end
@app.route("/")
def chatbox():
    return render_template_string("""
        <!doctype html>
        <title>Chatbox Command Interface</title>
        <h1>Command Input</h1>
        <form action="/chatbox" method="post">
            <input type="text" name="command" placeholder="Enter command (e.g., /balance)" required>
            <button type="submit">Send</button>
        </form>
        <br>
        <h1>Set License Key</h1>
        <form action="/chatbox" method="post">
            <input type="text" name="command" placeholder="Enter /set_license <license_key>" required>
            <button type="submit">Set License Key</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))