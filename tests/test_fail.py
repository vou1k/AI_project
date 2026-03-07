
import requests

def test_fail_for_chat():
    r = requests.get("http://localhost:5000/api/test")
    # намеренно неправильная проверка чтобы тест упал
    assert r.status_code == 404
