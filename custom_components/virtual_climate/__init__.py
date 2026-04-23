"""Virtual Climate integration."""

from __future__ import annotations

from collections.abc import Callable

import voluptuous as vol
from homeassistant.components.climate import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_CLIMATE_NAMES,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TARGET_TEMPERATURE,
    DEFAULT_CURRENT_TEMPERATURE,
    DEFAULT_HUMIDITY,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
    SERVICE_SET_AVAILABILITY,
    SERVICE_SET_CURRENT_TEMPERATURE,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_WINDOW_OPEN,
)
from .models import VirtualClimateState

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the domain."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})
    climates = _build_climate_states(entry)
    update_listeners: dict[str, set[Callable[[], None]]] = {key: set() for key in climates}
    hass.data[DOMAIN][entry.entry_id] = {
        "climates": climates,
        "listeners": update_listeners,
        "remove_listener": entry.add_update_listener(_async_handle_entry_update),
    }
    _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        stored = hass.data[DOMAIN].pop(entry.entry_id, None)
        if stored is not None:
            stored["remove_listener"]()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_CURRENT_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_AVAILABILITY)
            hass.services.async_remove(DOMAIN, SERVICE_SET_HUMIDITY)
            hass.services.async_remove(DOMAIN, SERVICE_SET_WINDOW_OPEN)
    return unload_ok


def _build_climate_states(entry: ConfigEntry) -> dict[str, VirtualClimateState]:
    """Build climate runtime state from entry data."""
    climate_names = _parse_climate_names(entry.data[CONF_CLIMATE_NAMES])
    current_temperature = float(
        entry.data.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMPERATURE)
    )
    target_temperature = float(
        entry.data.get(CONF_INITIAL_TARGET_TEMPERATURE, DEFAULT_TARGET_TEMPERATURE)
    )
    climates: dict[str, VirtualClimateState] = {}
    for index, name in enumerate(climate_names):
        climates[str(index)] = VirtualClimateState(
            name=name,
            current_temperature=current_temperature,
            target_temperature=target_temperature,
            hvac_mode=HVACMode.HEAT,
            humidity=DEFAULT_HUMIDITY,
        )
    return climates


def _parse_climate_names(raw_value: str) -> list[str]:
    """Parse a comma-separated list of climate entity names."""
    names = [item.strip() for item in raw_value.split(",")]
    normalized = [item for item in names if item]
    if not normalized:
        raise ValueError("At least one climate name is required")
    return normalized


def _async_register_services(hass: HomeAssistant) -> None:
    """Register helper services once."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_CURRENT_TEMPERATURE):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CURRENT_TEMPERATURE,
        _async_handle_set_current_temperature,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required("temperature"): vol.Coerce(float),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AVAILABILITY,
        _async_handle_set_availability,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required("available"): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HUMIDITY,
        _async_handle_set_humidity,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required("humidity"): vol.Coerce(float),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WINDOW_OPEN,
        _async_handle_set_window_open,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required("open"): cv.boolean,
            }
        ),
    )


async def _async_handle_set_current_temperature(service_call: ServiceCall) -> None:
    """Update the simulated current temperature."""
    await _async_update_matching_entities(
        service_call.hass,
        service_call.data[ATTR_ENTITY_ID],
        lambda state: setattr(state, "current_temperature", service_call.data["temperature"]),
    )


async def _async_handle_set_availability(service_call: ServiceCall) -> None:
    """Update the simulated availability."""
    await _async_update_matching_entities(
        service_call.hass,
        service_call.data[ATTR_ENTITY_ID],
        lambda state: setattr(state, "available", service_call.data["available"]),
    )


async def _async_handle_set_humidity(service_call: ServiceCall) -> None:
    """Update the simulated humidity."""
    await _async_update_matching_entities(
        service_call.hass,
        service_call.data[ATTR_ENTITY_ID],
        lambda state: setattr(state, "humidity", service_call.data["humidity"]),
    )


async def _async_handle_set_window_open(service_call: ServiceCall) -> None:
    """Update the simulated window-contact state."""
    await _async_update_matching_entities(
        service_call.hass,
        service_call.data[ATTR_ENTITY_ID],
        lambda state: setattr(state, "window_open", service_call.data["open"]),
    )


async def _async_update_matching_entities(
    hass: HomeAssistant,
    entity_ids: list[str],
    updater: Callable[[VirtualClimateState], None],
) -> None:
    """Apply an update function to matching runtime states and notify listeners."""
    entity_registry = er.async_get(hass)
    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None or entity_entry.platform != DOMAIN:
            continue
        config_entry_id = entity_entry.config_entry_id
        unique_id = entity_entry.unique_id
        if config_entry_id is None or not unique_id.startswith(f"{config_entry_id}_"):
            continue

        state_key = unique_id.removeprefix(f"{config_entry_id}_")
        state_id = state_key.split("_", 1)[0]
        stored = hass.data[DOMAIN].get(config_entry_id)
        if stored is None:
            continue
        state = stored["climates"].get(state_id)
        if state is None:
            continue

        updater(state)
        _async_notify_listeners(stored["listeners"][state_id])


@callback
def async_get_entry_state(
    hass: HomeAssistant,
    entry_id: str,
) -> tuple[dict[str, VirtualClimateState], dict[str, set[Callable[[], None]]]]:
    """Return runtime state and listeners for an entry."""
    stored = hass.data[DOMAIN][entry_id]
    return stored["climates"], stored["listeners"]


@callback
def _async_notify_listeners(listeners: set[Callable[[], None]]) -> None:
    for listener in listeners:
        listener()


async def _async_handle_entry_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after options changes."""
    await hass.config_entries.async_reload(entry.entry_id)
