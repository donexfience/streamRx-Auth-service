from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import aiosmtplib
import os
from typing import Optional

class EmailServiceUseCase:
    def __init__(
        self,
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port = int(os.getenv("SMTP_PORT", 587)),
        username = os.getenv("SMTP_USER", "your-email@gmail.com"),
        password = os.getenv("SMTP_PASSWORD", "your-app-specific-password"),
        use_tls = bool(os.getenv("SMTP_USE_TLS", True))

    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_verification_email(self, to_email: str, otp: str) -> None:
        """
        Send verification email with OTP to user
        """
        message = MIMEMultipart()
        message["From"] = self.username
        message["To"] = to_email
        message["Subject"] = "Verify Your Email Address"

        body = f"""
        Hello,

        Thank you for registering! Please use the following verification code to complete your registration:

        {otp}

        This code will expire in 30 minutes.

        If you didn't request this verification, please ignore this email.

        Best regards,
        Your Application Team
        """

        message.attach(MIMEText(body, "plain"))

        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls
            ) as smtp:
                await smtp.login(self.username, self.password)
                await smtp.send_message(message)
        except Exception as e:
            # In a production environment, if we wwant to log this error
            raise RuntimeError(f"Failed to send email: {str(e)}")