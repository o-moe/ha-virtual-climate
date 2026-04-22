"""Climate platform for Virtual Climate."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import async_get_entry_state
from .const import DOMAIN
from .models import VirtualClimateState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up climate entities from a config entry."""
    climates, listeners = async_get_entry_state(hass, entry.entry_id)
    async_add_entities(
        [
            VirtualClimateEntity(entry.entry_id, state_id, climates[state_id], listeners[state_id])
            for state_id in climates
        ]
    )


class VirtualClimateEntity(RestoreEntity, ClimateEntity):
    """A simple in-memory virtual climate entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 5.0
    _attr_max_temp = 35.0
    _attr_target_temperature_step = 0.5

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
        self._attr_name = state.name
        self._attr_unique_id = f"{entry_id}_{state_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Virtual Climate",
        }

    async def async_added_to_hass(self) -> None:
        """Restore state and subscribe to runtime changes."""
        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_target = last_state.attributes.get("temperature")
            if isinstance(restored_target, int | float):
                self._state.target_temperature = float(restored_target)
            restored_hvac_mode = last_state.state
            with suppress(ValueError):
                self._state.hvac_mode = HVACMode(restored_hvac_mode)
        self._listeners.add(self._handle_runtime_update)
        self.async_on_remove(lambda: self._listeners.discard(self._handle_runtime_update))

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._state.available

    @property
    def current_temperature(self) -> float:
        """Return the simulated current temperature."""
        return self._state.current_temperature

    @property
    def target_temperature(self) -> float:
        """Return the simulated target temperature."""
        return self._state.target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self._state.hvac_mode

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the target temperature."""
        temperature = kwargs.get("temperature")
        if isinstance(temperature, int | float):
            self._state.target_temperature = float(temperature)
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        self._state.hvac_mode = hvac_mode
        self.async_write_ha_state()

    @callback
    def _handle_runtime_update(self) -> None:
        self.async_write_ha_state()
