"""Парсинг и валидация JSON из AI ответов"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class JSONParser:
    """Извлечение и парсинг JSON из текста"""

    @staticmethod
    def extract_json(text: str) -> str:
        """Извлечь JSON из текста"""
        text = text.strip()
        
        # Удалить markdown код блоки
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        
        # Найти JSON объект в фигурных скобках
        start = text.find('{')
        if start == -1:
            return text
            
        # Правильный поиск конца JSON - находим последнюю }
        end = text.rfind('}')
        if end != -1 and end > start:
            return text[start:end+1].strip()
        
        return text

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Парсить JSON и вернуть dict"""
        try:
            json_text = JSONParser.extract_json(text)
            # Очистить от потенциальных ошибок (неправильные кавычки и т.д.)
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"Текст для парсинга: {text[:500]}")
            raise
