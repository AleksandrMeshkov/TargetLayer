import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.settings.settings import settings


template_path = Path(__file__).parent / "templates" / "recovery_email.html"


class MessageSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465
        self.sender_email = settings.EMAIL_ADDRESS
        self.sender_password = settings.EMAIL_PASSWORD
        self.timeout = 30

    async def send_recovery_link(self, email: str, token: str) -> bool:
        try:
            subject = "Восстановление пароля TargetLayer"

            if template_path.exists():
                html = template_path.read_text(encoding="utf-8")
            else:
                html = (
                    f"<p>Здравствуйте!</p>"
                    f"<p>Токен восстановления: <strong>{token}</strong></p>"
                )

            html = html.replace("{{ token }}", token)
            if "{{ url }}" in html:
                url = settings.FRONTEND_URL or ""
                html = html.replace("{{ url }}", url)

            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = email
            message["Subject"] = subject

            text_body = f"Ваш токен восстановления: {token}"
            message.attach(MIMEText(text_body, "plain", "utf-8"))
            message.attach(MIMEText(html, "html", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.smtp_server,
                self.smtp_port,
                context=context,
                timeout=self.timeout,
            ) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            return True
        except Exception as e:
            print(f"Ошибка при отправке письма: {e}")
            return False
