import os
import hashlib
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
URL = "https://www.ufmg.br/copeve/site_novo/?pagina=1"
CHECKSUM_FILE = "webpage_checksum.txt"

# Email configuration loaded from .env
EMAIL_CONFIG = {
    "sender": os.getenv("EMAIL_SENDER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "receiver": os.getenv("EMAIL_RECEIVER")
}


def fetch_webpage(url):
    """Fetch the content of the webpage."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def extract_target_content(html):
    """Extract the content of the specific <div>."""
    soup = BeautifulSoup(html, "html.parser")
    target_div = soup.find("div", id="home")

    if target_div:
        return target_div.get_text(strip=True)  # Get text content of the target <div>
    else:
        raise ValueError("Target <div> not found on the webpage.")


def calculate_checksum(content):
    """Calculate a checksum of the content to detect changes."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def load_previous_checksum(file_path):
    """Load the previous checksum from a file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return file.read().strip()
    return None


def save_checksum(file_path, checksum):
    """Save the current checksum to a file."""
    with open(file_path, "w") as file:
        file.write(checksum)


def send_email(subject, body):
    """Send an email alert."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender"]
        msg["To"] = EMAIL_CONFIG["receiver"]
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.send_message(msg)

        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def monitor_website():
    """Monitor the website for changes."""
    print("Fetching the webpage...")
    content = fetch_webpage(URL)

    print("Extracting target content...")
    try:
        target_content = extract_target_content(content)
    except ValueError as e:
        print(e)
        return

    # Calculate the current checksum
    current_checksum = calculate_checksum(target_content)

    # Load the previous checksum
    previous_checksum = load_previous_checksum(CHECKSUM_FILE)

    if previous_checksum is None:
        print("No previous checksum found. Saving current state...")
        save_checksum(CHECKSUM_FILE, current_checksum)
    elif current_checksum != previous_checksum:
        print("Change detected! Sending alert...")
        send_email(
            subject="Website Change Detected",
            body=f"The specific section of the website has changed:\n\n{target_content}"
        )
        save_checksum(CHECKSUM_FILE, current_checksum)
    else:
        print("No changes detected.")


if __name__ == "__main__":
    # Check if all email variables are set
    if not all(EMAIL_CONFIG.values()):
        print("Error: Missing email configuration. Check your .env file.")
    else:
        monitor_website()
