import os
import requests
from flask import Flask, request, jsonify, render_template_string, redirect
from dotenv import load_dotenv

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
    redirect_url = None  # Initialize redirect_url variable

    print(f"Received command: {command}")  # Log the received command

    if command == "/balance":
        # Define the balance URL
        balance_url = "http://205.185.117.225:9203/check_balance?user=hKzK5lWvwG"
        print(f"Redirect URL: {balance_url}")  # Log the redirect URL
        redirect_url = balance_url  # Set the redirect_url to the balance URL

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

    # Return the message and optional redirect_url to the frontend
    return jsonify({"message": response_message, "redirect_url": redirect_url})

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
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chatbox Command Interface</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center px-4">
        <div class="bg-white shadow-lg rounded-2xl p-6 w-full max-w-md">
            <h1 class="text-2xl font-semibold mb-4 text-center text-blue-600">Command Interface</h1>
            <form id="chatboxForm" action="/chatbox" method="post" class="space-y-4">
                <input type="text" name="command" placeholder="Enter command (e.g., /balance)" required
                       class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400">
                <button type="submit"
                        class="w-full bg-blue-600 text-white font-medium py-2 rounded-lg hover:bg-blue-700 transition">
                    Send Command
                </button>
            </form>
            <p id="responseMessage" class="mt-4 text-sm text-gray-700 whitespace-pre-line"></p>
        </div>

        <script>
            const form = document.getElementById("chatboxForm");
            form.onsubmit = async (event) => {
                event.preventDefault();
                const formData = new FormData(form);
                const response = await fetch("/chatbox", {
                    method: "POST",
                    body: formData
                });
                const result = await response.json();
                if (result.redirect_url) {
                    window.location.href = result.redirect_url;
                } else {
                    document.getElementById("responseMessage").textContent = result.message || "An error occurred.";
                }
            };
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
