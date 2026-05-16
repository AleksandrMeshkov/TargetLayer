import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.settings.settings import settings


recovery_template_path = Path(__file__).parent / "templates" / "recovery_email.html"
invite_template_path = Path(__file__).parent / "templates" / "team_invite_email.html"


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
            recovery_url = settings.build_frontend_recovery_url(token)

            if recovery_template_path.exists():
                html = recovery_template_path.read_text(encoding="utf-8")
            else:
                html = (
                    f"<p>Здравствуйте!</p>"
                    f"<p>Перейдите по ссылке для восстановления пароля:</p>"
                    f"<p><a href=\"{recovery_url}\">Восстановить пароль</a></p>"
                )

            html = html.replace("{{ token }}", token)
            if "{{ url }}" in html:
                html = html.replace("{{ url }}", recovery_url)

            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = email
            message["Subject"] = subject

            text_body = (
                "Вы запросили восстановление пароля. "
                f"Перейдите по ссылке: {recovery_url}"
            )
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

    async def send_team_invite_link(self, email: str, token: str) -> bool:
        try:
            subject = "Приглашение в команду TargetLayer"
            invite_url = settings.build_backend_team_invite_accept_url(token)

            if invite_template_path.exists():
                html = invite_template_path.read_text(encoding="utf-8")
            else:
                html = (
                    f"<p>Здравствуйте!</p>"
                    f"<p>Вас пригласили в команду. Перейдите по ссылке, чтобы принять приглашение:</p>"
                    f"<p><a href=\"{invite_url}\">Принять приглашение</a></p>"
                )

            html = html.replace("{{ token }}", token)
            if "{{ url }}" in html:
                html = html.replace("{{ url }}", invite_url)

            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = email
            message["Subject"] = subject

            text_body = (
                "Вас пригласили в команду. "
                f"Перейдите по ссылке: {invite_url}"
            )
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
