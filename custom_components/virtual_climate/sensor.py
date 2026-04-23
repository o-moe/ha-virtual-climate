"""Sensor platform for Virtual Climate."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import async_get_entry_state
from .const import DOMAIN
from .models import VirtualClimateState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up humidity sensors from a config entry."""
    climates, listeners = async_get_entry_state(hass, entry.entry_id)
    async_add_entities(
        [
            VirtualClimateHumiditySensor(
                entry.entry_id,
                state_id,
                climates[state_id],
                listeners[state_id],
            )
            for state_id in climates
        ]
    )


class VirtualClimateHumiditySensor(SensorEntity):
    """A simple in-memory humidity sensor paired with a virtual climate."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry_id: str,
        state_id: str,
        state: VirtualClimateState,
        listeners: set[Callable[[], None]],
    ) -> None:
        self._entry_id = entry_id
        self._state_id = state_id
        self._state = state
        self._listeners = listeners
        self._attr_name = f"{state.name} Humidity"
        self._attr_unique_id = f"{entry_id}_{state_id}_humidity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry_id}_{state_id}")},
            "name": state.name,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime changes."""
        self._listeners.add(self._handle_runtime_update)
        self.async_on_remove(lambda: self._listeners.discard(self._handle_runtime_update))

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._state.available

    @property
    def native_value(self) -> float:
        """Return the simulated humidity."""
        return self._state.humidity

    @callback
    def _handle_runtime_update(self) -> None:
        self.async_write_ha_state()
