"""Config flow for Piazza HQ.

One step: host + port + the automation token generated in Piazza HQ's own
Settings -> Home Assistant Control. Validated with a real call before the
entry is created, so a typo or a stale/revoked token fails here with a
useful message instead of surfacing as an unavailable entity later.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PiazzaHQApiClient, PiazzaHQAuthError, PiazzaHQConnectionError
from .const import CONF_TOKEN, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_TOKEN): str,
    }
)


class PiazzaHQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Piazza HQ."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            token = user_input[CONF_TOKEN]

            session = async_get_clientsession(self.hass)
            client = PiazzaHQApiClient(session, host, port, token)
            try:
                await client.async_validate()
            except PiazzaHQAuthError:
                errors["base"] = "invalid_auth"
            except PiazzaHQConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - guard against anything unforeseen, not just our own errors
                _LOGGER.exception("Unexpected error validating Piazza HQ connection")
                errors["base"] = "unknown"
            else:
                # One Piazza HQ device per config entry — a household with a
                # host + mirrors would add each one separately, same as any
                # other multi-device integration. Unique id prevents the
                # same host:port being added twice by mistake.
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Piazza HQ ({host})",
                    data={CONF_HOST: host, CONF_PORT: port, CONF_TOKEN: token},
                )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
