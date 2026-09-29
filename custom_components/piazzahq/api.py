"""Thin async client for Piazza HQ's automation-token REST surface.

Wraps exactly the endpoints already documented for the REST/rest_command
door (POST .../tv/:action, POST saved-layouts/:id/apply) plus the read-only
discovery endpoints added alongside this integration (GET .../screens,
.../displays, .../saved-layouts) — see piazzahq/server.js's
AUTOMATION_CONTROL_ROUTES. No logic lives here beyond HTTP plumbing; every
action this integration exposes already exists and is already used by the
REST and MQTT doors.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


class PiazzaHQError(Exception):
    """Base error for anything that goes wrong talking to Piazza HQ."""


class PiazzaHQConnectionError(PiazzaHQError):
    """Couldn't reach the host at all (wrong IP/port, device offline)."""


class PiazzaHQAuthError(PiazzaHQError):
    """Reached the host, but the automation token was rejected."""


class PiazzaHQApiClient:
    """Talks to one Piazza HQ device over its automation-token REST door."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int, token: str) -> None:
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._token = token

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.request(method, url, headers=headers, json=json) as resp:
                    if resp.status == 401:
                        raise PiazzaHQAuthError(f"Automation token rejected by {self._base_url}")
                    resp.raise_for_status()
                    if resp.content_type == "application/json":
                        return await resp.json()
                    return None
        except PiazzaHQAuthError:
            raise
        except (asyncio.TimeoutError, aiohttp.ClientConnectionError) as err:
            raise PiazzaHQConnectionError(f"Could not reach {self._base_url}: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise PiazzaHQConnectionError(f"{self._base_url} returned HTTP {err.status}") from err

    async def async_get_screens(self) -> list[dict[str, str]]:
        """Screens with TV control configured — [{device_id, name}]."""
        return await self._request("GET", "/api/automation/screens")

    async def async_get_displays(self) -> list[dict[str, str]]:
        """Displays — [{slug, name}]."""
        return await self._request("GET", "/api/automation/displays")

    async def async_get_saved_layouts(self) -> list[dict[str, Any]]:
        """Saved layouts — [{id, name}]."""
        return await self._request("GET", "/api/automation/saved-layouts")

    async def async_tv_action(self, device_id: str, action: str) -> None:
        """action is 'power-on' or 'power-off'."""
        await self._request("POST", f"/api/screens/{device_id}/tv/{action}")

    async def async_apply_layout(self, layout_id: int, display_slug: str) -> None:
        await self._request(
            "POST", f"/api/saved-layouts/{layout_id}/apply", json={"mode": "current", "display": display_slug}
        )

    async def async_validate(self) -> None:
        """Cheapest real call that proves both connectivity and a valid token.

        Used by the config flow — raises PiazzaHQConnectionError or
        PiazzaHQAuthError on failure, returns nothing on success.
        """
        await self.async_get_screens()
