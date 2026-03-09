import requests

print("🔄 Тестируем Pollinations.ai...")

# Самый простой GET запрос
url = "https://text.pollinations.ai/Привет, это тест! Ответь кратко."
response = requests.get(url)

print(f"Статус: {response.status_code}")
print(f"Ответ: {response.text[:200]}")