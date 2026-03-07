"""
Automatically generated tests (MVP, dedup + parametrized)
Total tests: 3
"""

import os
import pytest
import requests

DEFAULT_BASE_URL = "http://localhost:5000"

@pytest.fixture(scope="session")
def base_url():
    return os.getenv("BASE_URL", DEFAULT_BASE_URL)

@pytest.fixture()
def session():
    return requests.Session()


TEST_CASES = [
    {'id': 'req_1_positive', 'requirement_id': 'REQ-1', 'title': 'Positive: Feature', 'type': 'positive', 'steps': ["Выполнить действие для 'Feature' с валидными данными", 'Проверить успешный ответ'], 'expected_result': 'HTTP 200/201 (успех)', 'method': 'GET', 'path': '/api/test', 'payload': None, 'expected_codes': [200, 201, 204]},
    {'id': 'req_1_negative', 'requirement_id': 'REQ-1', 'title': 'Negative: Feature', 'type': 'negative', 'steps': ["Выполнить действие для 'Feature' с невалидными данными", 'Проверить 4xx ответ'], 'expected_result': 'HTTP 4xx (ошибка валидации/доступа)', 'method': 'GET', 'path': '/api/test', 'payload': None, 'expected_codes': [400, 401, 403, 404, 409, 422]},
    {'id': 'req_1_boundary', 'requirement_id': 'REQ-1', 'title': 'Boundary: Feature', 'type': 'boundary', 'steps': ["Выполнить действие для 'Feature' с граничными значениями", 'Проверить отсутствие 500'], 'expected_result': 'Система корректно обрабатывает крайние значения (нет 500)', 'method': 'GET', 'path': '/api/test', 'payload': None, 'expected_codes': [200, 201, 204, 400, 401, 403, 404, 409, 422]},
]


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["id"] for c in TEST_CASES])
def test_generated(case, session, base_url):
    """Single parametrized test for all generated cases (MVP)."""
    url = f"{base_url}{case['path']}"
    method = case['method']
    payload = case.get('payload')

    # If still on demo endpoint, negative/boundary are not meaningful -> skip (honest MVP)
    if case['path'] == '/api/test' and case['type'] in ('negative', 'boundary'):
        pytest.skip("MVP: demo endpoint /api/test doesn't support invalid/boundary inputs yet")

    if payload is None:
        resp = session.request(method, url, timeout=10)
    else:
        resp = session.request(method, url, json=payload, timeout=10)

    if case['type'] == 'boundary':
        assert resp.status_code != 500, f"Boundary must not crash server. got={resp.status_code}"
    else:
        assert resp.status_code in case['expected_codes'], (
            f"Unexpected status {resp.status_code}. expected one of {case['expected_codes']}"
        )

    # Demo endpoint contract
    if case['path'] == '/api/test' and resp.headers.get('content-type','').startswith('application/json'):
        body = resp.json()
        assert body.get('status') == 'ok'
