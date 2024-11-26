from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import aiosmtplib
import os
from typing import Optional

load_dotenv()
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
    
    async def send_password_change_email(self,to_email:str,reset_link:str) ->None:
        message = MIMEMultipart()
        message["From"] = self.username
        message["To"] = to_email
        message["Subject"] = "Forgot password link "
        print(reset_link,"reset ilnk got")
        html_content = f"""
        <html>
        <body>
            <div style="background-color: #f5f5f5; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                    <div style="text-align: center;">
                        <img src="https://via.placeholder.com/150" alt="Logo" style="max-width: 150px;">
                        <h2 style="color: #333;">Reset your password</h2>
                    </div>
                    <p>We've got a request from you to reset the password for your account. Please click on the button below to get a new password.</p>
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="{reset_link}" style="display: inline-block; background-color: #007bff; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px;">Reset my password</a>
                    </div>
                    <p>Questions? Please let us know if there's anything we can help you with by replying to this email or by emailing <a href="mailto:help@company.com">help@company.com</a>.</p>
                    <p>If you didn't request a password reset, we recommend you get in touch with our support team and secure your account.</p>
                    <p>Call us at +1 (877) 678-9789 or write to us at <a href="mailto:help@company.com">help@company.com</a>.</p>
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="https://www.facebook.com/company" style="margin-right: 10px;"><img src="https://via.placeholder.com/30" alt="Facebook"></a>
                        <a href="https://www.instagram.com/company" style="margin-right: 10px;"><img src="https://via.placeholder.com/30" alt="Instagram"></a>
                        <a href="https://twitter.com/company" style="margin-right: 10px;"><img src="https://via.placeholder.com/30" alt="Twitter"></a>
                    </div>
                    <p style="font-size: 12px; color: #999; text-align: center;">Copyright © 2022 Company. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        message.attach(MIMEText(html_content, "html"))
        
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