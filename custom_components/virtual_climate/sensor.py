"""Sensor platform for Virtual Climate."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
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
    """Set up sensor entities from a config entry."""
    climates, listeners = async_get_entry_state(hass, entry.entry_id)
    async_add_entities(
        [
            entity
            for state_id in climates
            for entity in (
                VirtualClimateTemperatureSensor(
                    entry.entry_id,
                    state_id,
                    climates[state_id],
                    listeners[state_id],
                ),
                VirtualClimateHumiditySensor(
                    entry.entry_id,
                    state_id,
                    climates[state_id],
                    listeners[state_id],
                ),
            )
        ]
    )


class _VirtualClimateBaseSensor(SensorEntity):
    """Shared base for in-memory sensors paired with a virtual climate."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry_id: str,
        state_id: str,
        state: VirtualClimateState,
        listeners: set[Callable[[], None]],
    ) -> None:
        self._state = state
        self._listeners = listeners
        self._set_identity(entry_id, state_id, state)

    def _set_identity(
        self,
        entry_id: str,
        state_id: str,
        state: VirtualClimateState,
    ) -> None:
        """Assign entity name, unique id, and device info."""
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime changes."""
        self._listeners.add(self._handle_runtime_update)
        self.async_on_remove(lambda: self._listeners.discard(self._handle_runtime_update))

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._state.available

    @callback
    def _handle_runtime_update(self) -> None:
        self.async_write_ha_state()


class VirtualClimateTemperatureSensor(_VirtualClimateBaseSensor):
    """A simple in-memory temperature sensor paired with a virtual climate."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def _set_identity(
        self,
        entry_id: str,
        state_id: str,
        state: VirtualClimateState,
    ) -> None:
        self._attr_name = f"{state.name} Temperature"
        self._attr_unique_id = f"{entry_id}_{state_id}_temperature"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry_id}_{state_id}")},
            "name": state.name,
        }

    @property
    def native_value(self) -> float:
        """Return the simulated current temperature."""
        return self._state.current_temperature


class VirtualClimateHumiditySensor(_VirtualClimateBaseSensor):
    """A simple in-memory humidity sensor paired with a virtual climate."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE

    def _set_identity(
        self,
        entry_id: str,
        state_id: str,
        state: VirtualClimateState,
    ) -> None:
        self._attr_name = f"{state.name} Humidity"
        self._attr_unique_id = f"{entry_id}_{state_id}_humidity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry_id}_{state_id}")},
            "name": state.name,
        }

    @property
    def native_value(self) -> float:
        """Return the simulated humidity."""
        return self._state.humidity
