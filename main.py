import os
import requests
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Get the TLO API Key from environment variables
CORRECT_API_KEY = os.getenv("TLO_API_KEY")
if not CORRECT_API_KEY:
    raise ValueError("TLO_API_KEY is required. Please set it in your environment.")

# Get the Discord Webhook URL from environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is required. Please set it in your environment.")

# Set the BASE_URL
BASE_URL = "https://webapp2-494f.onrender.com"

# Initialize Flask app
app = Flask(__name__)

# Initialize ThreadPoolExecutor for concurrent tasks
executor = ThreadPoolExecutor(max_workers=5)

def send_request(endpoint, timeout=10):
    """ Helper to send HTTP requests quickly """
    try:
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in request: {e}")
        return {"error": "Request failed"}

def send_to_discord_async(title, description, color=3447003):
    """ Send Discord notification asynchronously """
    def task():
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
            if not response.ok:
                print(f"Discord webhook failed: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Discord: {e}")
    executor.submit(task)

@app.route("/check_api_key", methods=["POST"])
def check_api_key():
    """ Validate the provided API key """
    entered_key = request.form.get("api_key", "").strip()
    if entered_key == CORRECT_API_KEY:
        return jsonify({"message": "API Key is valid!"})
    else:
        return jsonify({"message": "Invalid API Key. Please try again."})

@app.route("/chatbox", methods=["POST"])
def chatbox_command():
    """ Handle chatbox commands """
    command = request.form.get("command", "").strip().lower()
    response_message = ""

    if command == "/balance":
        url = f"{BASE_URL}/check_balance?license_key={CORRECT_API_KEY}"
        result = send_request(url)
        response_message = f"Balance Info: {result}" if result else "Failed to check balance."

    elif command.startswith("/email_lookup"):
        parts = command.split()
        if len(parts) != 2:
            response_message = "Usage: /email_lookup <email>"
        else:
            email = parts[1]
            url = f"{BASE_URL}/email_lookup?email={email}&license_key={CORRECT_API_KEY}"
            result = send_request(url)
            response_message = f"Email Lookup Result for {email}: {result}" if result else "Failed to perform email lookup."

    elif command.startswith("/ssn_lookup"):
        parts = command.split()
        if len(parts) != 4:
            response_message = "Usage: /ssn_lookup <first_name> <last_name> <dob>"
        else:
            fname, lname, dob = parts[1], parts[2], parts[3]
            url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={CORRECT_API_KEY}"
            result = send_request(url)
            response_message = f"SSN Lookup Result for {fname} {lname} (DOB: {dob}): {result}" if result else "Failed to perform SSN lookup."

    else:
        response_message = "Unknown command. Available commands: /balance, /email_lookup, /ssn_lookup"

    send_to_discord_async("Chatbox Command Response", response_message)
    return jsonify({"message": response_message})

@app.route("/enter_api_key", methods=["GET", "POST"])
def enter_api_key():
    """ Enter and validate API key """
    if request.method == "POST":
        api_key = request.form.get("api_key").strip()
        if api_key == CORRECT_API_KEY:
            return jsonify({"message": "API Key is valid!"})
        else:
            return jsonify({"message": "Invalid API Key. Please try again."})

    return render_template_string("""
        <!doctype html>
        <title>Enter API Key</title>
        <h1>Enter Your TLO API Key</h1>
        <form action="/enter_api_key" method="post">
            <input type="text" name="api_key" placeholder="Enter API Key" required>
            <button type="submit">Check API Key</button>
        </form>
    """)

@app.route("/")
def chatbox():
    """ Chatbox front-end """
    return render_template_string("""
        <!doctype html>
        <title>Chatbox Command Interface</title>
        <h1>Command Input</h1>
        <form action="/chatbox" method="post">
            <input type="text" name="command" placeholder="Enter command (e.g., /balance)" required>
            <button type="submit">Send</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
