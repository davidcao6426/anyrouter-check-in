"""代理配置：读取环境变量并供浏览器 / HTTP 客户端使用。"""

from __future__ import annotations

import os
from urllib.parse import unquote, urlsplit


def get_proxy_server(*, use_proxy: bool = True) -> str | None:
	"""按平台配置读取 CHECKIN_PROXY_URL；use_proxy=False 时不返回代理地址。"""
	if not use_proxy:
		return None
	server = os.getenv('CHECKIN_PROXY_URL', '').strip()
	return server or None


def get_playwright_proxy(*, use_proxy: bool = True) -> dict[str, str] | None:
	proxy_url = get_proxy_server(use_proxy=use_proxy)
	if not proxy_url:
		return None

	parsed = urlsplit(proxy_url)
	if parsed.username is None:
		return {'server': proxy_url}

	if not parsed.scheme or not parsed.hostname:
		return {'server': proxy_url}

	host = parsed.hostname
	if ':' in host and not host.startswith('['):
		host = f'[{host}]'

	server = f'{parsed.scheme}://{host}'
	if parsed.port is not None:
		server += f':{parsed.port}'

	proxy = {
		'server': server,
		'username': unquote(parsed.username),
	}
	if parsed.password is not None:
		proxy['password'] = unquote(parsed.password)
	return proxy
