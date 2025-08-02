import os
import requests
from flask import Flask, request, jsonify, render_template_string, redirect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CORRECT_API_KEY = "hKzK5lWvwG"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL is required. Please set it in your environment.")

BASE_URL = "http://205.185.117.225:9203"
app = Flask(__name__)

def send_to_discord(title, description, color=3447003):
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
        print("Notification sent to Discord." if response.ok else f"Failed: {response.text}")
    except requests.exceptions.RequestException as e:
        print("Error sending to Discord:", e)

@app.route("/check_api_key", methods=["POST"])
def check_api_key():
    entered_key = request.form.get("api_key", "").strip()
    return jsonify({"message": "API Key is valid!" if entered_key == CORRECT_API_KEY else "Invalid API Key. Please try again."})

@app.route("/chatbox", methods=["POST"])
def chatbox_command():
    command = request.form.get("command", "").strip().lower()
    response_message = ""
    redirect_url = None

    print(f"Received command: {command}")

    try:
        if command == "/balance":
            redirect_url = f"{BASE_URL}/check_balance?user={CORRECT_API_KEY}"

        elif command.startswith("/email_lookup"):
            parts = command.split()
            if len(parts) == 2:
                email = parts[1]
                url = f"{BASE_URL}/email_lookup?email={email}&license_key={CORRECT_API_KEY}"
                response = requests.get(url)
                response.raise_for_status()
                response_message = f"Email Lookup: {response.json()}"
            else:
                response_message = "Usage: /email_lookup <email>"

        elif command.startswith("/ssn_lookup"):
            parts = command.split()
            if len(parts) == 4:
                fname, lname, dob = parts[1], parts[2], parts[3]
                url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={CORRECT_API_KEY}"
                response = requests.get(url)
                response.raise_for_status()
                response_message = f"SSN Lookup: {response.json()}"
            else:
                response_message = "Usage: /ssn_lookup <first_name> <last_name> <dob>"

        elif command.startswith("/phone_lookup"):
            parts = command.split()
            if len(parts) == 2:
                phone = parts[1]
                url = f"{BASE_URL}/phone_lookup?phone={phone}&license_key={CORRECT_API_KEY}"
                response = requests.get(url)
                response.raise_for_status()
                response_message = f"Phone Lookup: {response.json()}"
            else:
                response_message = "Usage: /phone_lookup <phone_number>"

        elif command.startswith("/ip_lookup"):
            parts = command.split()
            if len(parts) == 2:
                ip = parts[1]
                response = requests.get(f"https://ipapi.co/{ip}/json/")
                response.raise_for_status()
                response_message = f"IP Lookup: {response.json()}"
            else:
                response_message = "Usage: /ip_lookup <ip_address>"

        elif command.startswith("/domain_lookup"):
            parts = command.split()
            if len(parts) == 2:
                domain = parts[1]
                response = requests.get(
                    f"https://api.api-ninjas.com/v1/whois?domain={domain}",
                    headers={"X-Api-Key": os.getenv("NINJA_API_KEY", "")})
                response.raise_for_status()
                response_message = f"Domain Lookup: {response.json()}"
            else:
                response_message = "Usage: /domain_lookup <domain>"

        elif command.startswith("/bin_lookup"):
            parts = command.split()
            if len(parts) == 2:
                bin_number = parts[1]
                response = requests.get(f"https://lookup.binlist.net/{bin_number}")
                response.raise_for_status()
                response_message = f"BIN Lookup: {response.json()}"
            else:
                response_message = "Usage: /bin_lookup <bin_number>"

        else:
            response_message = "Unknown command. Try: /balance, /email_lookup, /ssn_lookup, /phone_lookup, /ip_lookup, /domain_lookup, /bin_lookup"

    except requests.exceptions.RequestException as e:
        response_message = f"An error occurred: {e}"

    send_to_discord("Chatbox Command Response", response_message)
    return jsonify({"message": response_message, "redirect_url": redirect_url})

@app.route("/enter_api_key", methods=["GET", "POST"])
def enter_api_key():
    if request.method == "POST":
        api_key = request.form.get("api_key").strip()
        return jsonify({"message": "API Key is valid!" if api_key == CORRECT_API_KEY else "Invalid API Key."})

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
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Chatbox Command Interface</title>
        <script src=\"https://cdn.tailwindcss.com\"></script>
    </head>
    <body class=\"bg-gray-100 min-h-screen flex items-center justify-center px-4\">
        <div class=\"bg-white shadow-lg rounded-2xl p-6 w-full max-w-md\">
            <h1 class=\"text-2xl font-semibold mb-4 text-center text-blue-600\">Command Interface</h1>
            <form id=\"chatboxForm\" action=\"/chatbox\" method=\"post\" class=\"space-y-4\">
                <input type=\"text\" name=\"command\" placeholder=\"Enter command (e.g., /balance)\" required
                       class=\"w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400\">
                <button type=\"submit\"
                        class=\"w-full bg-blue-600 text-white font-medium py-2 rounded-lg hover:bg-blue-700 transition\">
                    Send Command
                </button>
            </form>
            <div class=\"mt-4 p-3 border border-gray-300 rounded-lg text-sm bg-gray-50\">
                <strong>Available Commands:</strong>
                <ul class=\"list-disc ml-5 mt-1 space-y-1\">
                    <li>/balance</li>
                    <li>/email_lookup &lt;email&gt;</li>
                    <li>/ssn_lookup &lt;first_name&gt; &lt;last_name&gt; &lt;dob&gt;</li>
                    <li>/phone_lookup &lt;phone_number&gt;</li>
                    <li>/ip_lookup &lt;ip_address&gt;</li>
                    <li>/domain_lookup &lt;domain.com&gt;</li>
                    <li>/bin_lookup &lt;bin_number&gt;</li>
                </ul>
            </div>
            <p id=\"responseMessage\" class=\"mt-4 text-sm text-gray-700 whitespace-pre-line\"></p>
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