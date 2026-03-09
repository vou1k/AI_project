from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests
import time

app = FastAPI(title="AI Test Platform")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Хранилище сессий
sessions = {}

class PollinationsAI:
    def __init__(self):
        print("=" * 60)
        print("🤖 POLLINATIONS AI С КОНТЕКСТОМ ТЕСТОВ")
        print("=" * 60)
        self.base_url = "https://text.pollinations.ai/"
        self.history = []
        self._check_connection()
    
    def _check_connection(self):
        """Проверка соединения с Pollinations"""
        try:
            response = requests.get(
                f"{self.base_url}Привет, это тест!",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Pollinations API: ПОДКЛЮЧЕНО")
            else:
                print(f"⚠️ Pollinations API ошибка: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Pollinations API предупреждение: {e}")
    
    def analyze_error(self, error_info=None, test_cases=None, results=None):
        """Анализ ошибки с контекстом тестов"""
        
        # Формируем подробный контекст
        context = "📊 **КОНТЕКСТ ТЕСТИРОВАНИЯ**\n\n"
        
        if test_cases:
            context += f"**Всего тестов:** {len(test_cases)}\n"
            context += "**Типы тестов:**\n"
            pos = sum(1 for t in test_cases if t.get('type') == 'positive')
            neg = sum(1 for t in test_cases if t.get('type') == 'negative')
            bound = sum(1 for t in test_cases if t.get('type') == 'boundary')
            context += f"- Позитивных: {pos}\n- Негативных: {neg}\n- Граничных: {bound}\n\n"
            
            # Показываем первые 5 тестов
            context += "**Примеры тестов:**\n"
            for tc in test_cases[:5]:
                context += f"• {tc.get('title', 'Без названия')} ({tc.get('type', 'unknown')})\n"
            context += "\n"
        
        if results:
            context += f"**РЕЗУЛЬТАТЫ:**\n"
            context += f"- Всего запущено: {results.get('total', 0)}\n"
            context += f"- ✅ Прошло: {results.get('passed', 0)}\n"
            context += f"- ❌ Упало: {results.get('failed', 0)}\n"
            context += f"- ⚠️ Ошибок: {results.get('errors', 0)}\n\n"
        
        if error_info and error_info.get('failed_tests'):
            context += "**❌ УПАВШИЕ ТЕСТЫ:**\n"
            for failed in error_info['failed_tests'][:3]:
                test_id = failed.get('test_id', 'unknown')
                error_msg = failed.get('error', 'Нет информации')
                context += f"• {test_id}: {error_msg}\n"
                
                # Добавляем рекомендации если есть
                suggestions = error_info.get('suggestions', {}).get(test_id, [])
                if suggestions:
                    context += f"  Рекомендации: {', '.join(suggestions[:2])}\n"
            context += "\n"
        
        prompt = f"""Ты AI ассистент для тестировщиков. Вот полный контекст тестирования:

{context}

Проанализируй ситуацию и дай КОНКРЕТНЫЕ рекомендации:
1. Что можно улучшить в тестах
2. Какие еще тесты стоит добавить
3. Как исправить упавшие тесты

Ответь подробно на русском языке."""
        
        return self._ask_pollinations(prompt)
    
    def chat(self, message, error_info=None, test_cases=None, results=None):
        """Ответ на сообщение с контекстом"""
        
        self.history.append({"role": "user", "content": message})
        
        # Формируем контекст
        context = "📊 **ТЕКУЩИЙ КОНТЕКСТ:**\n"
        
        if test_cases:
            context += f"• Всего тестов: {len(test_cases)}\n"
        
        if results:
            context += f"• Прошло: {results.get('passed', 0)}/{results.get('total', 0)}\n"
        
        if error_info and error_info.get('failed_tests'):
            context += f"• Упало: {len(error_info['failed_tests'])}\n"
        
        prompt = f"""Ты AI ассистент для тестировщиков. Вот контекст:

{context}

Вопрос пользователя: {message}

Дай КОНКРЕТНЫЙ ответ, основанный на контексте тестирования. 
Если спрашивают про улучшение тестов - предложи конкретные идеи.
Если спрашивают про ошибки - объясни причину и как исправить.

Ответь на русском языке."""
        
        response = self._ask_pollinations(prompt)
        self.history.append({"role": "assistant", "content": response})
        return response
    
    def _ask_pollinations(self, prompt):
        """Отправка запроса в Pollinations"""
        print(f"\n📤 ОТПРАВКА В POLLINATIONS")
        
        try:
            response = requests.get(
                f"{self.base_url}{prompt}",
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.text.strip()
                print(f"✅ ПОЛУЧЕН ОТВЕТ: {answer[:100]}...")
                return answer
            else:
                return f"⚠️ Ошибка API: {response.status_code}"
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return f"⚠️ Ошибка соединения. Но я вижу контекст: у вас {len(test_cases) if test_cases else 0} тестов. Что именно хотите улучшить?"
    
    def get_history(self):
        return self.history

# Инициализация AI
ai = PollinationsAI()

@app.get("/")
async def root():
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла"""
    try:
        session_id = f"session_{len(sessions) + 1}"
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Парсим требования из файла
        requirements = []
        lines = text_content.split('\n')
        
        req_id = "REQ-001"
        req_title = "User Authentication"
        req_desc = ""
        ac_list = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "Requirement" in line or "REQ" in line:
                if ac_list:
                    requirements.append({
                        "id": req_id,
                        "title": req_title,
                        "description": req_desc,
                        "acceptance_criteria": ac_list
                    })
                # Новое требование
                parts = line.split('(')
                req_id = parts[1].replace(')', '') if len(parts) > 1 else "REQ-001"
                req_title = line.replace(f"({req_id})", "").replace("Requirement", "").strip()
                ac_list = []
            elif line.startswith('-') or 'AC' in line:
                ac_list.append(line.lstrip('- '))
            elif line.startswith('Description'):
                req_desc = line.replace('Description', '').strip()
        
        # Добавляем последнее требование
        if req_id and ac_list:
            requirements.append({
                "id": req_id,
                "title": req_title,
                "description": req_desc,
                "acceptance_criteria": ac_list
            })
        
        # Генерируем тест-кейсы
        test_cases = []
        for req in requirements:
            for i, ac in enumerate(req['acceptance_criteria']):
                # Позитивный тест
                test_cases.append({
                    "id": f"{req['id']}_POS_{i+1}",
                    "requirement_id": req['id'],
                    "title": f"Позитивный тест: {ac[:50]}",
                    "type": "positive",
                    "steps": ["Подготовить данные", "Выполнить действие", "Проверить результат"],
                    "expected_result": ac
                })
                # Негативный тест
                test_cases.append({
                    "id": f"{req['id']}_NEG_{i+1}",
                    "requirement_id": req['id'],
                    "title": f"Негативный тест: {ac[:50]}",
                    "type": "negative",
                    "steps": ["Подготовить невалидные данные", "Выполнить действие", "Проверить ошибку"],
                    "expected_result": "Ошибка"
                })
                # Граничный тест
                test_cases.append({
                    "id": f"{req['id']}_BND_{i+1}",
                    "requirement_id": req['id'],
                    "title": f"Граничный тест: {ac[:50]}",
                    "type": "boundary",
                    "steps": ["Подготовить граничные значения", "Выполнить действие", "Проверить обработку"],
                    "expected_result": "Граничное значение обработано"
                })
        
        # Сохраняем сессию
        sessions[session_id] = {
            "id": session_id,
            "file": file.filename,
            "created_at": time.time(),
            "requirements": requirements,
            "test_cases": test_cases
        }
        
        print(f"\n✅ СЕССИЯ СОЗДАНА: {session_id}")
        print(f"📊 Требований: {len(requirements)}")
        print(f"🧪 Тест-кейсов: {len(test_cases)}")
        print(f"📊 АКТИВНЫЕ СЕССИИ: {list(sessions.keys())}")
        
        return JSONResponse({
            "session_id": session_id,
            "requirements": requirements,
            "test_cases": test_cases
        })
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/{session_id}")
async def generate_tests(session_id: str):
    """Генерация тестов"""
    print(f"\n📋 Генерация для сессии: {session_id}")
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse({
        "test_cases": sessions[session_id]["test_cases"],
        "code": {
            "code": "# Сгенерированные тесты\nimport pytest\n\ndef test_example():\n    assert True",
            "framework": "pytest",
            "test_count": len(sessions[session_id]["test_cases"])
        }
    })

@app.post("/api/run/{session_id}")
async def run_tests(session_id: str):
    """Запуск тестов"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    test_cases = sessions[session_id]["test_cases"]
    
    # Имитируем результаты (70% проходят, 30% падают)
    import random
    random.seed(hash(session_id))
    
    results = []
    passed = 0
    failed = 0
    
    for tc in test_cases:
        if random.random() < 0.7:
            results.append({"test_id": tc["id"], "status": "passed", "duration": 0.1})
            passed += 1
        else:
            results.append({
                "test_id": tc["id"], 
                "status": "failed", 
                "duration": 0.1,
                "error_message": f"AssertionError: Expected {tc['expected_result']}"
            })
            failed += 1
    
    sessions[session_id]["results"] = {
        "total": len(test_cases),
        "passed": passed,
        "failed": failed,
        "errors": 0,
        "results": results
    }
    
    return JSONResponse(sessions[session_id]["results"])

@app.post("/api/debug/{session_id}")
async def debug_results(session_id: str):
    """Анализ результатов"""
    print(f"\n🔍 Анализ для сессии: {session_id}")
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    results = session.get("results", {})
    test_cases = session.get("test_cases", [])
    
    # Формируем debug информацию
    failed_tests = []
    root_causes = {}
    suggestions = {}
    is_app_bug = {}
    
    for r in results.get("results", []):
        if r["status"] == "failed":
            failed_tests.append({
                "test_id": r["test_id"],
                "error": r.get("error_message", "Unknown error")
            })
            root_causes[r["test_id"]] = "API вернул неожиданный ответ"
            suggestions[r["test_id"]] = [
                "Проверьте что сервер запущен",
                "Проверьте тестовые данные",
                "Проверьте логи приложения"
            ]
            is_app_bug[r["test_id"]] = True
    
    debug_info = {
        "failed_tests": failed_tests,
        "root_causes": root_causes,
        "suggestions": suggestions,
        "is_app_bug": is_app_bug
    }
    
    session["debug"] = debug_info
    
    # Анализируем через AI с контекстом
    analysis = ai.analyze_error(debug_info, test_cases, results)
    session["ai_analysis"] = analysis
    
    return JSONResponse(debug_info)

@app.post("/api/chat/{session_id}")
async def chat_with_ai(session_id: str, request: dict):
    """Чат с Pollinations AI"""
    print(f"\n{'='*60}")
    print(f"💬 ЧАТ ДЛЯ СЕССИИ: {session_id}")
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    user_message = request.get("message", "")
    
    print(f"📊 Тестов в сессии: {len(session.get('test_cases', []))}")
    
    # Получаем контекст
    error_info = session.get("debug")
    test_cases = session.get("test_cases")
    results = session.get("results")
    
    if not user_message:
        # Первое сообщение - анализ
        response = ai.analyze_error(error_info, test_cases, results)
    else:
        # Ответ на вопрос с контекстом
        response = ai.chat(user_message, error_info, test_cases, results)
    
    print(f"{'='*60}\n")
    
    return JSONResponse({
        "response": response,
        "history": ai.get_history()
    })

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК AI TEST PLATFORM")
    print("🤖 POLLINATIONS AI С КОНТЕКСТОМ")
    print("📊 http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)