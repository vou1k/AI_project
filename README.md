```markdown
# AI-система для анализа и синтеза знаний из научных публикаций

Интеллектуальная платформа для анализа корпуса научных статей с использованием современных AI-технологий, включая интеграцию с Pollinations.ai для генерации контента.

## Возможности

- 🔍 **Интеллектуальный анализ** научных публикаций
- 🤖 **Интеграция с Pollinations.ai** для генерации и синтеза информации
- 📊 **Тестирование AI-моделей** на платформе
- 📑 **Работа с научными текстами** и метаданными
- ⚡ **Быстрый поиск** по корпусу документов

## Архитектура проекта

📦 AI-Knowledge-Synthesis
├── 📁 backend
│ └── 📁 app
│ └── 📄 main.py # Точка входа API
├── 📁 demo_app # Демонстрационное приложение
├── 📁 tests # Тесты проекта
├── 📄 ai_test_platform.py # Основная платформа для тестирования AI
├── 📄 ai_test_platform.pyproj # Проектный файл Python
├── 📄 ai_test_platform.sln # Solution file
├── 📄 test_requirements.txt # Зависимости для тестирования
└── 📄 .gitignore # Исключения Git

## Быстрый старт

### Предварительные требования

- Python 3.8 или выше
- Установленный pip

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/vou1k/AI_project/tree/working-version.git
cd your-repo
```

2. **Установите основные зависимости:**
```bash
pip install -r requirements.txt
```

3. **Установите зависимости для тестирования (опционально):**
```bash
pip install -r test_requirements.txt
```

### Запуск проекта

1. **Запустите backend сервер (терминал 1):**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

2. **Запустите demo приложение (терминал 2):**
```bash
cd demo_app
python app.py
```

3. **Откройте приложение в браузере:**
```
http://localhost:8000
```

## Интеграция с Pollinations.ai

Проект использует [Pollinations.ai](https://pollinations.ai) для генерации текста и синтеза информации. Для работы с API:

1. Получите API ключ на платформе Pollinations.ai
2. Настройте переменные окружения или конфигурацию в `ai_test_platform.py`

## Тестирование

Для запуска тестов используйте:

```bash
python -m pytest tests/
```

Или запустите основную тестовую платформу:

```bash
python ai_test_platform.py
```

## API Endpoints

После запуска backend доступна документация API:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Основные endpoints:

- `GET /` - Health check
- `POST /analyze` - Анализ научной публикации
- `POST /search` - Поиск по корпусу документов
- `POST /generate` - Генерация ответа с использованием Pollinations.ai

## Разработка

### Настройка окружения разработчика

1. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
pip install -r test_requirements.txt
```

3. **Настройте переменные окружения:**
```bash
export POLLINATIONS_API_KEY="your-api-key"
# или создайте .env файл
```

## Структура кода

- **ai_test_platform.py** - Основная логика платформы тестирования AI
- **backend/app/main.py** - FastAPI приложение и роутинг
- **demo_app/** - Примеры использования и демонстрационный интерфейс
- **tests/** - Модульные и интеграционные тесты

```
