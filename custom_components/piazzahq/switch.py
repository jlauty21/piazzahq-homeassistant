"""Screen power switches -- one per Piazza HQ screen with TV control set up.

Mirrors the MQTT door's own Power switch exactly (see mqtt-bridge.js
publishSwitches()): a TV/monitor's real on/off state generally can't be
queried back (most TV remotes have no "are you on" signal to ask, which is
also true for CEC on many sets), so this is a command-only, optimistic
switch -- assumed_state=True tells Home Assistant's own UI to show it that
way, the same honest limitation both other doors already document.
"""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PiazzaHQCoordinator
from .const import DOMAIN, MANUFACTURER


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: PiazzaHQCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_ids: set[str] = set()

    def _add_new_entities() -> None:
        new_entities = [
            PiazzaHQScreenSwitch(coordinator, entry, screen["device_id"], screen["name"])
            for screen in coordinator.data.screens
            if screen["device_id"] not in known_ids
        ]
        if new_entities:
            known_ids.update(e.device_id for e in new_entities)
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class PiazzaHQScreenSwitch(CoordinatorEntity[PiazzaHQCoordinator], SwitchEntity):
    """Turns a screen's TV/monitor on or off."""

    _attr_has_entity_name = True
    _attr_translation_key = "screen_power"
    _attr_assumed_state = True

    def __init__(self, coordinator: PiazzaHQCoordinator, entry: ConfigEntry, device_id: str, name: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}_tv_power"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=name,
            manufacturer=MANUFACTURER,
            model="Screen",
        )
        # There's no real state to report (see module docstring) -- start
        # False rather than None so the UI shows a definite toggle position
        # instead of an "unknown" state from the moment it's added.
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.async_tv_action(self.device_id, "power-on")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.async_tv_action(self.device_id, "power-off")
        self._attr_is_on = False
        self.async_write_ha_state()
