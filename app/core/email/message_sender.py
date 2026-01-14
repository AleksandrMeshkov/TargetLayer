import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.settings.settings import settings


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
            
            body = f"""Здравствуйте!

Вы запросили восстановление пароля для вашего аккаунта.

Токен восстановления: {token}

Используйте этот токен для установки нового пароля.

Если это были не вы, то проигнорируйте это письмо.

С уважением,
TargetLayer Team"""
            
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain", "utf-8"))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=self.timeout) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"Ошибка при отправке письма: {str(e)}")
            return False
