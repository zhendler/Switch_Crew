from fastapi_mail import ConnectionConfig

from config.general import settings
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


def send_verification_grid(email: str, email_body: str):
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