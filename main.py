import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env for local development
load_dotenv()

# Get the base URL dynamically from Render's environment variable or use localhost for local testing
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000")

# Secrets stored in Render or .env for local development
API_KEY = os.getenv("TLO_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not API_KEY:
    raise EnvironmentError("API_KEY is not set. Please add it to your environment variables.")
if not DISCORD_WEBHOOK_URL:
    raise EnvironmentError("DISCORD_WEBHOOK_URL is not set. Please add it to your environment variables.")

def debug_request(endpoint):
    """ Helper to send requests and print detailed debugging info """
    try:
        print(f"Requesting URL: {endpoint}")
        response = requests.get(endpoint, timeout=10)
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)

        if response.ok:
            return response.json()
        else:
            print("Error:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return None

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

def check_balance():
    print("\n--- Checking Balance ---")
    url = f"{BASE_URL}/check_balance?license_key={API_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord("Balance Check", f"Balance Info: {result}")

def email_lookup(email):
    print("\n--- Performing Email Lookup ---")
    if not email:
        print("Error: Email is required")
        return
    url = f"{BASE_URL}/email_lookup?email={email}&license_key={API_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord("Email Lookup", f"Email Lookup Result for {email}: {result}")

def ssn_lookup(fname, lname, dob):
    print("\n--- Performing SSN Lookup ---")
    if not all([fname, lname, dob]):
        print("Error: First name, last name, and DOB are required")
        return
    url = f"{BASE_URL}/ssn?fname={fname}&lname={lname}&dob={dob}&license_key={API_KEY}"
    result = debug_request(url)
    if result:
        send_to_discord(
            "SSN Lookup",
            f"SSN Lookup Result for {fname} {lname} (DOB: {dob}): {result}"
        )

def main():
    print("TLO API Debug Tool\n")

    check_balance()
    email_lookup("test@example.com")
    ssn_lookup("John", "Doe", "01-01-2000")

if __name__ == "__main__":
    main()