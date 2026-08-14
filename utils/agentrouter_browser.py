from typing import Any


def build_playwright_cookies(
	cookies: dict[str, str],
	provider_url: str,
	*,
	excluded_names: set[str] | None = None,
) -> list[dict[str, str]]:
	"""Convert simple cookie mapping to Playwright cookie objects scoped to provider URL."""
	excluded = excluded_names or set()
	return [
		{'name': name, 'value': value, 'url': provider_url}
		for name, value in cookies.items()
		if name and value and name not in excluded
	]


def parse_user_info_payload(payload: object) -> dict | None:
	"""Convert AgentRouter /api/user/self payload to the existing balance result shape."""
	if not isinstance(payload, dict) or payload.get('success') is not True:
		return None

	user_data = payload.get('data')
	if not isinstance(user_data, dict):
		return None

	quota = round(user_data.get('quota', 0) / 500000, 2)
	used_quota = round(user_data.get('used_quota', 0) / 500000, 2)
	return {
		'success': True,
		'quota': quota,
		'used_quota': used_quota,
		'display': f':money: Current balance: ${quota}, Used: ${used_quota}',
	}


async def get_user_info_with_browser(
	account_name: str,
	provider_config: Any,
	user_cookies: dict[str, str],
	api_user: str | None,
	*,
	timeout_ms: int = 120_000,
) -> dict:
	"""Request AgentRouter user info inside the same stealth browser session that passes WAF."""
	from cloakbrowser import launch_async

	from utils.browser import prepare_browser_page, wait_for_waf_ready
	from utils.proxy import get_playwright_proxy

	launch_kwargs: dict = {'headless': True}
	proxy = get_playwright_proxy(use_proxy=provider_config.use_proxy)
	if proxy:
		launch_kwargs['proxy'] = proxy

	print(f'[PROCESSING] {account_name}: Requesting AgentRouter user info inside browser...')
	browser = await launch_async(**launch_kwargs)
	try:
		page = await browser.new_page()
		await prepare_browser_page(page)

		# Do not import stale WAF cookies copied from a previous browser session.
		# Let the current stealth browser obtain a fresh WAF cookie itself.
		waf_cookie_names = set(provider_config.waf_cookie_names or [])
		browser_cookies = build_playwright_cookies(
			user_cookies,
			provider_config.domain,
			excluded_names=waf_cookie_names,
		)
		if browser_cookies:
			await page.context.add_cookies(browser_cookies)

		login_url = f'{provider_config.domain}{provider_config.login_path}'
		await page.goto(login_url, wait_until='domcontentloaded', timeout=min(timeout_ms, 60_000))
		await wait_for_waf_ready(page, timeout_ms=min(timeout_ms, 60_000))

		result = await page.evaluate(
			"""async ({ path, apiUserKey, apiUser }) => {
				const headers = {
					'Accept': 'application/json, text/plain, */*',
					'X-Requested-With': 'XMLHttpRequest',
				};
				if (apiUser) headers[apiUserKey] = apiUser;

				const response = await fetch(path, {
					method: 'GET',
					credentials: 'include',
					cache: 'no-store',
					headers,
				});
				const contentType = response.headers.get('content-type') || '';
				let payload = null;
				if (contentType.includes('application/json')) {
					try { payload = await response.json(); } catch (_) { payload = null; }
				}
				return {
					status: response.status,
					contentType,
					allow: response.headers.get('allow') || '',
					payload,
				};
			} """,
			{
				'path': provider_config.user_info_path,
				'apiUserKey': provider_config.api_user_key,
				'apiUser': api_user,
			},
		)

		status = int(result.get('status', 0)) if isinstance(result, dict) else 0
		content_type = result.get('contentType', '') if isinstance(result, dict) else ''
		allow = result.get('allow', '') if isinstance(result, dict) else ''
		print(f'[INFO] {account_name}: Browser user info response HTTP {status}')

		if status != 200:
			details = f', content-type={content_type}' if content_type else ''
			if allow:
				details += f', allow={allow}'
			return {'success': False, 'error': f'Failed to get user info: HTTP {status} (browser{details})'}

		parsed = parse_user_info_payload(result.get('payload') if isinstance(result, dict) else None)
		if parsed:
			return parsed

		return {
			'success': False,
			'error': f'Failed to get user info: invalid browser response (content-type={content_type or "unknown"})',
		}
	except Exception as e:
		return {'success': False, 'error': f'Failed to get user info in browser: {str(e)[:80]}'}
	finally:
		await browser.close()
