"""Tests for Virtual Climate entities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from homeassistant.components.climate import HVACMode

from custom_components.virtual_climate.binary_sensor import VirtualClimateWindowSensor
from custom_components.virtual_climate.climate import VirtualClimateEntity
from custom_components.virtual_climate.models import VirtualClimateState
from custom_components.virtual_climate.sensor import (
    VirtualClimateHumiditySensor,
    VirtualClimateTemperatureSensor,
)


class VirtualClimateEntityTests(IsolatedAsyncioTestCase):
    """Test the climate entity behavior."""

    async def test_entity_updates_target_and_hvac_mode(self) -> None:
        state = VirtualClimateState(
            name="Living Room",
            current_temperature=20.0,
            target_temperature=21.0,
            hvac_mode=HVACMode.HEAT,
        )
        entity = VirtualClimateEntity("entry-1", "0", state, set())
        entity.async_write_ha_state = Mock()

        await entity.async_set_temperature(temperature=22.5)
        await entity.async_set_hvac_mode(HVACMode.AUTO)

        self.assertEqual(entity.target_temperature, 22.5)
        self.assertEqual(entity.hvac_mode, HVACMode.AUTO)

    async def test_entity_exposes_availability(self) -> None:
        state = VirtualClimateState(
            name="Office",
            current_temperature=19.0,
            target_temperature=20.0,
            hvac_mode=HVACMode.HEAT,
            available=False,
        )
        entity = VirtualClimateEntity("entry-1", "0", state, set())

        self.assertFalse(entity.available)

    async def test_entity_restores_last_state_and_registers_listener(self) -> None:
        listeners: set = set()
        state = VirtualClimateState(
            name="Bedroom",
            current_temperature=18.0,
            target_temperature=20.0,
            hvac_mode=HVACMode.HEAT,
        )
        entity = VirtualClimateEntity("entry-1", "0", state, listeners)
        entity.async_get_last_state = AsyncMock(
            return_value=SimpleNamespace(
                state=HVACMode.AUTO,
                attributes={"temperature": 23.0},
            )
        )
        entity.async_on_remove = Mock()

        await entity.async_added_to_hass()

        self.assertEqual(entity.target_temperature, 23.0)
        self.assertEqual(entity.hvac_mode, HVACMode.AUTO)
        self.assertIn(entity._handle_runtime_update, listeners)

    async def test_humidity_sensor_exposes_runtime_state(self) -> None:
        listeners: set = set()
        state = VirtualClimateState(
            name="Living Room",
            current_temperature=20.0,
            target_temperature=21.0,
            hvac_mode=HVACMode.HEAT,
            humidity=52.0,
        )
        entity = VirtualClimateHumiditySensor("entry-1", "0", state, listeners)
        entity.async_on_remove = Mock()

        await entity.async_added_to_hass()

        self.assertEqual(entity.native_value, 52.0)
        self.assertIn(entity._handle_runtime_update, listeners)

    async def test_temperature_sensor_exposes_runtime_state(self) -> None:
        listeners: set = set()
        state = VirtualClimateState(
            name="Living Room",
            current_temperature=20.0,
            target_temperature=21.0,
            hvac_mode=HVACMode.HEAT,
        )
        entity = VirtualClimateTemperatureSensor("entry-1", "0", state, listeners)
        entity.async_on_remove = Mock()

        await entity.async_added_to_hass()

        self.assertEqual(entity.native_value, 20.0)
        self.assertIn(entity._handle_runtime_update, listeners)

    async def test_window_sensor_exposes_runtime_state(self) -> None:
        listeners: set = set()
        state = VirtualClimateState(
            name="Living Room",
            current_temperature=20.0,
            target_temperature=21.0,
            hvac_mode=HVACMode.HEAT,
            window_open=True,
        )
        entity = VirtualClimateWindowSensor("entry-1", "0", state, listeners)
        entity.async_on_remove = Mock()

        await entity.async_added_to_hass()

        self.assertTrue(entity.is_on)
        self.assertIn(entity._handle_runtime_update, listeners)
