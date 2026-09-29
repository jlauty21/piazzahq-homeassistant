"""Layout selects -- one per Piazza HQ display, options = saved layout names.

Selecting an option applies that saved layout (widgets + theme) to the
display -- the same action the REST rest_command door's step 3 and the MQTT
door's own Layout select both already perform.

Optimistic, like the switch above and like the MQTT door's own select
(mqtt-bridge.js publishSelects()): there is no stored link anywhere in
Piazza HQ between "a display's current widgets" and "which saved layout that
came from" (someone could also hand-edit the layout afterward), so this
can't truthfully report which preset is currently active -- only that the
last selection here was applied. assumed_state=True surfaces that honestly
in Home Assistant's own UI.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PiazzaHQCoordinator
from .const import DOMAIN, MANUFACTURER


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: PiazzaHQCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_slugs: set[str] = set()

    def _add_new_entities() -> None:
        new_entities = [
            PiazzaHQLayoutSelect(coordinator, entry, display["slug"], display["name"])
            for display in coordinator.data.displays
            if display["slug"] not in known_slugs
        ]
        if new_entities:
            known_slugs.update(e.display_slug for e in new_entities)
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


def _layout_options(saved_layouts: list[dict]) -> dict[str, int]:
    """Map a display label -> saved-layout id, disambiguating duplicate names.

    Saved-layout names aren't required to be unique in Piazza HQ itself, so
    two layouts named e.g. "Family Hub" would otherwise collide as HA select
    options -- append the id to any name that repeats, leaving the common
    case (all-unique names) exactly as typed in Piazza HQ.
    """
    counts: dict[str, int] = {}
    for layout in saved_layouts:
        counts[layout["name"]] = counts.get(layout["name"], 0) + 1
    return {
        (layout["name"] if counts[layout["name"]] == 1 else f"{layout['name']} (#{layout['id']})"): layout["id"]
        for layout in saved_layouts
    }


class PiazzaHQLayoutSelect(CoordinatorEntity[PiazzaHQCoordinator], SelectEntity):
    """Applies a saved layout (+ its theme) to a display."""

    _attr_has_entity_name = True
    _attr_translation_key = "display_layout"
    _attr_assumed_state = True

    def __init__(self, coordinator: PiazzaHQCoordinator, entry: ConfigEntry, display_slug: str, name: str) -> None:
        super().__init__(coordinator)
        self.display_slug = display_slug
        self._attr_unique_id = f"{entry.entry_id}_{display_slug}_layout"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, display_slug)},
            name=name,
            manufacturer=MANUFACTURER,
            model="Display",
        )
        self._attr_current_option = None

    @property
    def options(self) -> list[str]:
        return list(_layout_options(self.coordinator.data.saved_layouts).keys())

    async def async_select_option(self, option: str) -> None:
        layout_id = _layout_options(self.coordinator.data.saved_layouts).get(option)
        if layout_id is None:
            return
        await self.coordinator.client.async_apply_layout(layout_id, self.display_slug)
        self._attr_current_option = option
        self.async_write_ha_state()
