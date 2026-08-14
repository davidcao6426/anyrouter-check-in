def build_playwright_cookies(cookies: dict[str, str], provider_url: str) -> list[dict[str, str]]:
	"""Convert simple cookie mapping to Playwright cookie objects scoped to provider URL."""
	return [
		{'name': name, 'value': value, 'url': provider_url}
		for name, value in cookies.items()
		if name and value
	]
