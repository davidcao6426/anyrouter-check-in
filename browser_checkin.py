#!/usr/bin/env python3
"""Entry point that keeps AgentRouter cookie-based user-info requests inside CloakBrowser."""

import asyncio

import checkin
from utils.agentrouter_browser import get_user_info_with_browser


_original_check_in_account = checkin.check_in_account


async def check_in_account_with_agentrouter_browser(account, account_index, app_config):
	"""Use browser fetch only for AgentRouter session-cookie accounts; preserve all other behavior."""
	if account.provider != 'agentrouter' or account.has_login_credentials():
		return await _original_check_in_account(account, account_index, app_config)

	account_name = account.get_display_name(account_index)
	provider_config = app_config.get_provider(account.provider)
	if not provider_config:
		print(f'[FAILED] {account_name}: Provider "{account.provider}" not found in configuration')
		return False, None, None

	user_cookies = checkin.parse_cookies(account.cookies)
	if not user_cookies:
		print(f'[FAILED] {account_name}: Invalid configuration format')
		return False, None, None

	print(f'[INFO] {account_name}: AgentRouter browser transport enabled for /api/user/self')
	user_info_after = await get_user_info_with_browser(
		account_name,
		provider_config,
		user_cookies,
		account.api_user,
	)

	if user_info_after.get('success'):
		print(user_info_after['display'])
		print(f'[INFO] {account_name}: Check-in completed automatically inside browser')
		return True, None, user_info_after

	error = user_info_after.get('error', 'Unknown error')
	print(f'[FAILED] {account_name}: Browser check-in failed - {error}')
	return False, None, user_info_after


def run_main():
	checkin.check_in_account = check_in_account_with_agentrouter_browser
	checkin.run_main()


if __name__ == '__main__':
	run_main()
