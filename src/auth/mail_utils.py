"""
Mail Utility Module
This module provides utility functions for sending emails, specifically for email verification in the authentication
process. It utilizes the FastAPI Mail library for configuring and sending emails.
Components:
    - `mail_conf`: Configuration object for FastAPI Mail.
    - `send_verification`: Function to send an email verification message.
Dependencies:
    - FastAPI Mail: A library for sending emails using SMTP.
    - Settings: Application-specific configuration stored in `config.general`.
Usage:
    Call `send_verification` with an email address and an email body to send a verification email.
"""

from config.general import settings

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content


def send_verification_grid(email: str, email_body: str):
    """
    Sends a verification email to the specified email address using SendGrid.

    Args:
        email (str): The recipient's email address.
        email_body (str): The HTML content of the email to be sent.

    Raises:
        Exception: If an error occurs while sending the email, the exception details are logged.

    Returns:
        None
    """
    sg = sendgrid.SendGridAPIClient(settings.sendgrid_api)
    from_email = Email("krutsvitya@gmail.com")
    to_email = To(email)
    subject = "Please verify your email address"
    content = Content("text/html", email_body)

    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        print(f"Email sent to {email}. Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
