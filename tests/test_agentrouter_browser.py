from utils.agentrouter_browser import build_playwright_cookies


def test_build_playwright_cookies_uses_provider_url_and_preserves_cookie_values():
	cookies = {
		'session': 'session-value',
		'acw_tc': 'waf-value',
	}

	result = build_playwright_cookies(cookies, 'https://agentrouter.org')

	assert result == [
		{'name': 'session', 'value': 'session-value', 'url': 'https://agentrouter.org'},
		{'name': 'acw_tc', 'value': 'waf-value', 'url': 'https://agentrouter.org'},
	]
