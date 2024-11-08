import ssl
from email.message import EmailMessage
from datetime import datetime
import smtplib
import socket


SUBJECT = "Cyberus Security Alert!"
MESSAGE = f"Intrusion detected on {socket.gethostname()} at {datetime.now()}! Contingencies have been deployed."

SENDER = "<email address>"
SENDER_PASSWORD = "<google app password>"
RECIPIENT = "<email address>"


msg = EmailMessage()
msg.set_content(MESSAGE)
msg["Subject"] = "Security Alert!"
msg["From"] = SENDER
msg["To"] = RECIPIENT

context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(SENDER, SENDER_PASSWORD)
    server.sendmail(SENDER, RECIPIENT, msg.as_string())
