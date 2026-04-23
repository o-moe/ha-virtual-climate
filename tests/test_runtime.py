"""Tests for Virtual Climate helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import Mock, patch

from homeassistant.components.climate import HVACMode

from custom_components.virtual_climate import (
    _async_notify_listeners,
    _async_update_matching_entities,
    _build_climate_states,
    _parse_climate_names,
)
from custom_components.virtual_climate.const import (
    CONF_CLIMATE_NAMES,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TARGET_TEMPERATURE,
)
from custom_components.virtual_climate.models import VirtualClimateState


class ParseClimateNamesTests(TestCase):
    """Test helper parsing."""

    def test_parse_climate_names_trims_and_filters(self) -> None:
        self.assertEqual(
            _parse_climate_names(" Living Room, Office ,, Bedroom "),
            ["Living Room", "Office", "Bedroom"],
        )

    def test_parse_climate_names_rejects_empty_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one climate name"):
            _parse_climate_names(" , , ")

    def test_build_climate_states_creates_one_state_per_name(self) -> None:
        entry = type(
            "Entry",
            (),
            {
                "data": {
                    CONF_CLIMATE_NAMES: "Living Room, Office",
                    CONF_INITIAL_CURRENT_TEMPERATURE: 19.5,
                    CONF_INITIAL_TARGET_TEMPERATURE: 21.0,
                }
            },
        )()

        climates = _build_climate_states(entry)

        self.assertEqual(set(climates), {"0", "1"})
        self.assertEqual(climates["0"].name, "Living Room")
        self.assertEqual(climates["1"].name, "Office")
        self.assertEqual(climates["0"].current_temperature, 19.5)
        self.assertEqual(climates["0"].target_temperature, 21.0)
        self.assertEqual(climates["0"].humidity, 45.0)
        self.assertFalse(climates["0"].window_open)
        self.assertEqual(climates["0"].hvac_mode, HVACMode.HEAT)

    def test_notify_listeners_calls_all_callbacks(self) -> None:
        first = Mock()
        second = Mock()

        _async_notify_listeners({first, second})

        first.assert_called_once()
        second.assert_called_once()


class RuntimeUpdateTests(IsolatedAsyncioTestCase):
    """Test async runtime update helpers."""

    async def test_update_matching_entities_updates_runtime_state(self) -> None:
        hass = Mock()
        entity_registry = Mock()
        entity_registry.async_get.return_value = SimpleNamespace(
            platform="virtual_climate",
            config_entry_id="entry-1",
            unique_id="entry-1_0",
        )
        hass.data = {
            "virtual_climate": {
                "entry-1": {
                    "climates": {
                        "0": VirtualClimateState(
                            name="Living Room",
                            current_temperature=20.0,
                            target_temperature=21.0,
                            hvac_mode=HVACMode.HEAT,
                        )
                    },
                    "listeners": {"0": {Mock()}},
                }
            }
        }

        with patch(
            "custom_components.virtual_climate.er.async_get",
            return_value=entity_registry,
        ):
            await _async_update_matching_entities(
                hass,
                ["climate.virtual_climate_living_room"],
                lambda state: setattr(state, "available", False),
            )

        self.assertFalse(hass.data["virtual_climate"]["entry-1"]["climates"]["0"].available)

    async def test_update_matching_entities_supports_linked_sensor_unique_ids(self) -> None:
        hass = Mock()
        entity_registry = Mock()
        entity_registry.async_get.return_value = SimpleNamespace(
            platform="virtual_climate",
            config_entry_id="entry-1",
            unique_id="entry-1_0_humidity",
        )
        hass.data = {
            "virtual_climate": {
                "entry-1": {
                    "climates": {
                        "0": VirtualClimateState(
                            name="Living Room",
                            current_temperature=20.0,
                            target_temperature=21.0,
                            hvac_mode=HVACMode.HEAT,
                        )
                    },
                    "listeners": {"0": {Mock()}},
                }
            }
        }

        with patch(
            "custom_components.virtual_climate.er.async_get",
            return_value=entity_registry,
        ):
            await _async_update_matching_entities(
                hass,
                ["sensor.virtual_climate_living_room_humidity"],
                lambda state: setattr(state, "humidity", 52.0),
            )

        self.assertEqual(hass.data["virtual_climate"]["entry-1"]["climates"]["0"].humidity, 52.0)
