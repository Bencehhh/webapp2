import os
import requests
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from time import sleep

# Load environment variables from .env file
load_dotenv()

# Set the correct TLO API Key
CORRECT_API_KEY = "hKzK5lWvwG"  # Replace with your actual TLO API Key

# Get the Discord Webhook URL from environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Raise an error if the Discord Webhook URL is not set
if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is required. Please set it in your environment.")

BASE_URL = "http://205.185.117.225:9203"  # The base URL for the service

app = Flask(__name__)

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

@app.route("/check_api_key", methods=["POST"])
def check_api_key():
    entered_key = request.form.get("api_key", "").strip()
    if entered_key == CORRECT_API_KEY:
        return jsonify({"message": "API Key is valid!"})
    else:
        return jsonify({"message": "Invalid API Key. Please try again."})

@app.route("/chatbox", methods=["POST"])
def chatbox_command():
    command = request.form.get("command", "").strip().lower()
    response_message = ""

    if command == "/balance":
        # Define the balance URL
        balance_url = "http://205.185.117.225:9203/check_balance?user=hKzK5lWvwG"
        
        # Fetch the balance from the URL
        try:
            response = requests.get(balance_url, timeout=10)  # Set a timeout to avoid hanging
            if response.ok:
                # Parse the balance info
                balance_info = response.json()  # Assuming the response is JSON
                balance = balance_info.get("credits", "N/A")  # Extract the 'credits' field
                
                # Send the balance info to Discord
                send_to_discord("Balance Information", f"Your current balance is: {balance} credits.")
                
                # Return the balance and the redirect URL
                response_message = f"Your balance: {balance} credits. Redirecting to: {balance_url}"
                return jsonify({"redirect_url": balance_url, "message": response_message, "balance": balance})
            else:
                response_message = "Failed to check balance: Unable to fetch data."
                return jsonify({"message": response_message}), 500
        except requests.exceptions.RequestException as e:
            response_message = f"Failed to check balance: {str(e)}"
            return jsonify({"message": response_message}), 500

    elif command.startswith("/email_lookup"):
        parts = command.split()
        if len(parts) != 2:
            response_message = "Usage: /email_lookup <email>"
        else:
            email = parts[1]
            url = f"{BASE_URL}/email_lookup?email={email}&license_key={CORRECT_API_KEY}"
            response = requests.get(url)
            if response.ok:
                response_message = f"Email Lookup Result for {email}: {response.json()}"
            else:
                response_message = "Failed to perform email lookup."

    elif command.startswith("/ssn_lookup"):
        parts = command.split()
        if len(parts) != 4:
            response_message = "Usage: /ssn_lookup <first_name> <last_name> <dob>"
        else:
            fname, lname, dob = parts[1], parts[2], parts[3]
            url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={CORRECT_API_KEY}"
            response = requests.get(url)
            if response.ok:
                response_message = f"SSN Lookup Result for {fname} {lname} (DOB: {dob}): {response.json()}"
            else:
                response_message = "Failed to perform SSN lookup."

    else:
        response_message = "Unknown command. Available commands: /balance, /email_lookup, /ssn_lookup"

    send_to_discord("Chatbox Command Response", response_message)
    return jsonify({"message": response_message})

@app.route("/enter_api_key", methods=["GET", "POST"])
def enter_api_key():
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
