import random
import string
from typing import Optional

class VerificationCodeGenerator:
    
    
    CODE_LENGTH = 6
    CHARACTERS = string.digits 
    
    @staticmethod
    def generate_code() -> str:
        
        return "".join(random.choices(VerificationCodeGenerator.CHARACTERS, k=VerificationCodeGenerator.CODE_LENGTH))
    
    @staticmethod
    def validate_code_format(code: str) -> bool:
        
        if not code:
            return False
        return code.isdigit() and len(code) == VerificationCodeGenerator.CODE_LENGTH
