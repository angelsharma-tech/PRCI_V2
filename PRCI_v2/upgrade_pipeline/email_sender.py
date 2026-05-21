import smtplib
import os
from email.message import EmailMessage

def send_email_with_pdf(to_email, pdf_bytes, user_name):
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    if not sender_email or not app_password:
        raise ValueError("Email credentials (SENDER_EMAIL, APP_PASSWORD) not set in environment.")

    msg = EmailMessage()
    msg['Subject'] = f"Your CORE:AI Mental Health Report, {user_name}"
    msg['From'] = sender_email
    msg['To'] = to_email

    msg.set_content(f"Hello {user_name},\n\nPlease find your personalized mental health analysis report attached.\n\nRemember to prioritize your well-being. You've taken a great first step.\n\nStay strong 💙\n\nBest,\nThe CORE:AI Team")

    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"{user_name}_mental_health_report.pdf")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)

def send_email(receiver_email, pdf_path):
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        app_password = os.getenv("APP_PASSWORD")

        if not sender_email or not app_password:
            raise ValueError(
                "Missing email credentials. Set environment variables SENDER_EMAIL and APP_PASSWORD."
            )

        msg = EmailMessage()
        msg['Subject'] = "Your Mental Health Report"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        msg.set_content(
            "Hello,\n\nPlease find your personalized mental health report attached.\n\nStay well!"
        )

        # Attach PDF
        with open(pdf_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='pdf',
                filename='report.pdf'
            )

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        return True

    except Exception as e:
        print("Email error:", e)
        return False
