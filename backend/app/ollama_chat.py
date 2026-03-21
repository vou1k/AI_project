import requests
import json

class OllamaChat:
    def __init__(self, model="llama2", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.history = []
        self._check_connection()

    def _check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama доступен")
            else:
                print("⚠️ Ollama не отвечает")
        except:
            print("⚠️ Ollama не запущен")

    def _ask_ollama(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"Ошибка Ollama: {e}")
        return ""

    def analyze_error(self, error_info=None):
        prompt = "Проанализируй ошибку в тесте..."
        return self._ask_ollama(prompt)

    def chat(self, message, error_info=None):
        self.history.append({"role": "user", "content": message})
        response = self._ask_ollama(message)
        self.history.append({"role": "assistant", "content": response})
        return response