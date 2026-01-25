import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class JSONParser:

    @staticmethod
    def extract_json(text: str) -> str:
        text = text.strip()
        
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
        
        start = text.find('{')
        if start == -1:
            return text
            
        end = text.rfind('}')
        if end != -1 and end > start:
            return text[start:end+1].strip()
        
        return text

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        try:
            json_text = JSONParser.extract_json(text)
            data = json.loads(json_text)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"Текст для парсинга: {text[:500]}")
            raise
