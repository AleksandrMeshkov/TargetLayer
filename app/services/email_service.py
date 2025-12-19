import mailtrap as mt
from redis.asyncio import Redis
from app.core.settings.settings import settings
from app.core.security.code_generator import VerificationCodeGenerator

class EmailVerificationService:
    """Сервис для отправки и подтверждения кодов верификации через email"""
    
    # Время жизни кода в Redis (в секундах): 10 минут
    VERIFICATION_CODE_TTL = 600
    VERIFICATION_KEY_PREFIX = "verification"
    
    def __init__(self, redis: Redis):
       
        self.redis = redis
        # Инициализация Mailtrap клиента с API Token
        self.mail_client = mt.MailtrapClient(token=settings.MAILTRAP_API_TOKEN)

    def _get_redis_key(self, email: str) -> str:
        
        return f"{self.VERIFICATION_KEY_PREFIX}:{email}"

    async def send_verification_code(self, email: str) -> str:
        
        # 1. Генерируем код с помощью VerificationCodeGenerator
        code = VerificationCodeGenerator.generate_code()
        
        # 2. Сохраняем в Redis с ключом "verification:{email}" на определённое время
        redis_key = self._get_redis_key(email)
        await self.redis.setex(redis_key, self.VERIFICATION_CODE_TTL, code)
        
        # 3. Формируем и отправляем письмо через Mailtrap API
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">Код подтверждения TargetLayer</h2>
                    <p>Здравствуйте!</p>
                    <p>Ваш код подтверждения:</p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="margin: 0; color: #007bff; font-family: monospace; letter-spacing: 2px;">{code}</h1>
                    </div>
                    <p style="color: #666;">Код действует <strong>10 минут</strong>.</p>
                    <p style="color: #999; font-size: 12px;">Если вы этого не запрашивали, игнорируйте это письмо.</p>
                </div>
            </body>
        </html>
        """
        
        try:
            # Создаём письмо через Mailtrap API
            mail = mt.Mail(
                sender=mt.Address(
                    email=settings.MAILTRAP_SENDER_EMAIL,
                    name=settings.MAILTRAP_SENDER_NAME
                ),
                to=[mt.Address(email=email)],
                subject="Код подтверждения TargetLayer",
                html=html_body,
                category="Email Verification"
            )
            
            # Отправляем письмо
            response = self.mail_client.send(mail)
            return code
            
        except Exception as e:
            # Удаляем код из Redis если не удалось отправить письмо
            await self.redis.delete(redis_key)
            raise Exception(f"Failed to send verification email: {str(e)}")

    async def verify_code(self, email: str, code: str) -> bool:
        """
        Проверяет корректность введённого кода верификации
        
        Args:
            email: Email адрес
            code: Введённый пользователем код
            
        Returns:
            bool: True если код верный и не истёк, False в противном случае
        """
        # Валидируем формат кода
        if not VerificationCodeGenerator.validate_code_format(code):
            return False
        
        # Получаем сохранённый код из Redis
        redis_key = self._get_redis_key(email)
        saved_code = await self.redis.get(redis_key)
        
        # Проверяем совпадение и удаляем ключ
        if saved_code and saved_code == code:
            await self.redis.delete(redis_key)
            return True
        
        return False

    async def is_verification_pending(self, email: str) -> bool:
        """
        Проверяет, ожидается ли верификация для email адреса
        
        Args:
            email: Email адрес
            
        Returns:
            bool: True если в Redis есть незаконченная верификация
        """
        redis_key = self._get_redis_key(email)
        return await self.redis.exists(redis_key)

    async def get_remaining_ttl(self, email: str) -> int:
        """
        Получает оставшееся время жизни кода в Redis (в секундах)
        
        Args:
            email: Email адрес
            
        Returns:
            int: Оставшееся время в секундах или -1 если ключа нет
        """
        redis_key = self._get_redis_key(email)
        return await self.redis.ttl(redis_key)