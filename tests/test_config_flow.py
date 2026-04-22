"""Tests for the Virtual Climate config flow."""

from __future__ import annotations

from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from custom_components.virtual_climate.config_flow import (
    VirtualClimateConfigFlow,
    VirtualClimateOptionsFlow,
)
from custom_components.virtual_climate.const import (
    CONF_CLIMATE_NAMES,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TARGET_TEMPERATURE,
)


class ConfigFlowTests(IsolatedAsyncioTestCase):
    """Test config flow behavior."""

    async def test_user_step_creates_entry(self) -> None:
        flow = VirtualClimateConfigFlow()
        flow.async_create_entry = Mock(return_value={"type": "create_entry"})

        result = await flow.async_step_user(
            {
                "name": "Virtual Climate",
                CONF_CLIMATE_NAMES: "Living Room, Office",
                CONF_INITIAL_CURRENT_TEMPERATURE: 20.0,
                CONF_INITIAL_TARGET_TEMPERATURE: 21.0,
            }
        )

        self.assertEqual(result, {"type": "create_entry"})
        flow.async_create_entry.assert_called_once()

    async def test_user_step_rejects_empty_names(self) -> None:
        flow = VirtualClimateConfigFlow()
        flow.async_show_form = Mock(return_value={"type": "form"})

        await flow.async_step_user(
            {
                "name": "Virtual Climate",
                CONF_CLIMATE_NAMES: " , ",
                CONF_INITIAL_CURRENT_TEMPERATURE: 20.0,
                CONF_INITIAL_TARGET_TEMPERATURE: 21.0,
            }
        )

        self.assertEqual(
            flow.async_show_form.call_args.kwargs["errors"],
            {CONF_CLIMATE_NAMES: "climate_names_required"},
        )

    async def test_options_flow_creates_entry(self) -> None:
        config_entry = type(
            "ConfigEntry",
            (),
            {
                "data": {
                    "name": "Virtual Climate",
                    CONF_CLIMATE_NAMES: "Living Room",
                    CONF_INITIAL_CURRENT_TEMPERATURE: 20.0,
                    CONF_INITIAL_TARGET_TEMPERATURE: 21.0,
                },
                "options": {},
            },
        )()
        flow = VirtualClimateOptionsFlow(config_entry)
        flow.async_create_entry = Mock(return_value={"type": "create_entry"})

        result = await flow.async_step_init(
            {
                CONF_CLIMATE_NAMES: "Living Room, Office",
                CONF_INITIAL_CURRENT_TEMPERATURE: 19.0,
                CONF_INITIAL_TARGET_TEMPERATURE: 22.0,
            }
        )

        self.assertEqual(result, {"type": "create_entry"})
        flow.async_create_entry.assert_called_once()
