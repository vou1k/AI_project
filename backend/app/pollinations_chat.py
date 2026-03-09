"""
Pollinations AI - отдельный файл
"""

import requests

class PollinationsChat:
    def __init__(self):
        self.base_url = "https://text.pollinations.ai/"
        self.history = []
    
    def analyze_error(self, error_info=None, test_cases=None, results=None):
        """Анализ ошибки"""
        context = self._build_context(error_info, test_cases, results)
        prompt = f"{context}\n\nПроанализируй ситуацию и дай рекомендации. Ответь на русском."
        return self._ask(prompt)
    
    def chat(self, message, error_info=None, test_cases=None, results=None):
        """Ответ на сообщение"""
        self.history.append({"role": "user", "content": message})
        context = self._build_context(error_info, test_cases, results)
        prompt = f"{context}\n\nВопрос: {message}\n\nОтветь на русском."
        response = self._ask(prompt)
        self.history.append({"role": "assistant", "content": response})
        return response
    
    def _build_context(self, error_info, test_cases, results):
        """Сборка контекста"""
        context = f"Всего тестов: {len(test_cases) if test_cases else 0}\n"
        if results:
            context += f"Прошло: {results.get('passed', 0)}, Упало: {results.get('failed', 0)}\n"
        if error_info and error_info.get('failed_tests'):
            context += f"Упавшие тесты: {len(error_info['failed_tests'])}\n"
        return context
    
    def _ask(self, prompt):
        try:
            response = requests.get(f"{self.base_url}{prompt}", timeout=30)
            return response.text.strip() if response.status_code == 200 else "⚠️ Ошибка API"
        except:
            return "⚠️ Ошибка соединения"
    
    def get_history(self):
        return self.history