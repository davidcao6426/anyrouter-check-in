from utils.agentrouter_browser import build_playwright_cookies, parse_user_info_payload


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


def test_build_playwright_cookies_can_exclude_stale_waf_cookies():
	cookies = {
		'session': 'session-value',
		'acw_tc': 'stale-waf-value',
	}

	result = build_playwright_cookies(
		cookies,
		'https://agentrouter.org',
		excluded_names={'acw_tc'},
	)

	assert result == [
		{'name': 'session', 'value': 'session-value', 'url': 'https://agentrouter.org'},
	]


def test_parse_user_info_payload_matches_existing_balance_format():
	payload = {
		'success': True,
		'data': {
			'quota': 1_250_000,
			'used_quota': 250_000,
		},
	}

	assert parse_user_info_payload(payload) == {
		'success': True,
		'quota': 2.5,
		'used_quota': 0.5,
		'display': ':money: Current balance: $2.5, Used: $0.5',
	}
