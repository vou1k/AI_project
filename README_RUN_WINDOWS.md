# Windows запуск + чат после падения тестов

Этот архив = версия с добавленным **чат-диалогом после падения тестов** (Analyze Results открывает чат и пишет стартовый анализ) + фикс под Windows/Python 3.13 (без Rust).

## Запуск
PowerShell:
```
.\run.ps1
```
CMD:
```
run.cmd
```

UI:
- http://localhost:8000
Swagger:
- http://localhost:8000/docs
demo_app:
- http://localhost:5000

## Где лежит "обучение" на фиксах
backend/app/data/learned_fixes.jsonl
