from utils.proxy import get_playwright_proxy


def test_authenticated_proxy_splits_credentials(monkeypatch):
	monkeypatch.setenv('CHECKIN_PROXY_URL', 'http://user:p%40ss@example.com:8080')

	assert get_playwright_proxy() == {
		'server': 'http://example.com:8080',
		'username': 'user',
		'password': 'p@ss',
	}


def test_proxy_without_credentials_is_unchanged(monkeypatch):
	monkeypatch.setenv('CHECKIN_PROXY_URL', 'http://example.com:8080')

	assert get_playwright_proxy() == {'server': 'http://example.com:8080'}


def test_proxy_disabled_returns_none(monkeypatch):
	monkeypatch.setenv('CHECKIN_PROXY_URL', 'http://user:pass@example.com:8080')

	assert get_playwright_proxy(use_proxy=False) is None
