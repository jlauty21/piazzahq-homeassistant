"""The Piazza HQ integration.

Reuses the exact same underlying actions the REST (rest_command) and MQTT
doors already call in piazzahq/server.js -- turning a screen's TV/monitor on
or off, and applying a saved layout (which also switches light/dark theme)
to a display. This integration adds a third door: a native config flow and
real entities instead of hand-written YAML or a broker, discovering valid
screens/displays/saved-layouts on its own via the automation-token's
read-only endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PiazzaHQApiClient, PiazzaHQConnectionError, PiazzaHQAuthError
from .const import CONF_TOKEN, DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SELECT]


@dataclass
class PiazzaHQData:
    """What the coordinator fetches each cycle -- screens/displays/layouts."""

    screens: list[dict] = field(default_factory=list)
    displays: list[dict] = field(default_factory=list)
    saved_layouts: list[dict] = field(default_factory=list)


class PiazzaHQCoordinator(DataUpdateCoordinator[PiazzaHQData]):
    """Periodically re-discovers screens/displays/saved layouts.

    There is no push/webhook path back from Piazza HQ, and no live "current
    state" to poll either -- see the select entity's own docstring for why
    the layout selector is optimistic. This coordinator exists purely so a
    screen or saved layout added in Piazza HQ *after* setup shows up as a
    new entity without the household needing to reload the integration by
    hand.
    """

    def __init__(self, hass: HomeAssistant, client: PiazzaHQApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> PiazzaHQData:
        try:
            screens = await self.client.async_get_screens()
            displays = await self.client.async_get_displays()
            saved_layouts = await self.client.async_get_saved_layouts()
        except PiazzaHQAuthError as err:
            # A token revoked/regenerated from inside Piazza HQ after setup --
            # surfaces as the entry needing reauth rather than entities just
            # silently going unavailable with no indication why.
            raise UpdateFailed("Automation token no longer valid") from err
        except PiazzaHQConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return PiazzaHQData(screens=screens, displays=displays, saved_layouts=saved_layouts)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = PiazzaHQApiClient(session, entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_TOKEN])

    coordinator = PiazzaHQCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
