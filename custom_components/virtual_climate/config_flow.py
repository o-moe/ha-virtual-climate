"""Config flow for Virtual Climate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from . import _parse_climate_names
from .const import (
    CONF_CLIMATE_NAMES,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TARGET_TEMPERATURE,
    DEFAULT_CLIMATE_NAMES,
    DEFAULT_CURRENT_TEMPERATURE,
    DEFAULT_ENTRY_NAME,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
)


class VirtualClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                climate_names = _parse_climate_names(user_input[CONF_CLIMATE_NAMES])
                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": str(user_input["name"]).strip() or DEFAULT_ENTRY_NAME,
                        CONF_CLIMATE_NAMES: ", ".join(climate_names),
                        CONF_INITIAL_CURRENT_TEMPERATURE: float(
                            user_input[CONF_INITIAL_CURRENT_TEMPERATURE]
                        ),
                        CONF_INITIAL_TARGET_TEMPERATURE: float(
                            user_input[CONF_INITIAL_TARGET_TEMPERATURE]
                        ),
                    },
                )
            except ValueError:
                errors[CONF_CLIMATE_NAMES] = "climate_names_required"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(
                {
                    "name": DEFAULT_ENTRY_NAME,
                    CONF_CLIMATE_NAMES: DEFAULT_CLIMATE_NAMES,
                    CONF_INITIAL_CURRENT_TEMPERATURE: DEFAULT_CURRENT_TEMPERATURE,
                    CONF_INITIAL_TARGET_TEMPERATURE: DEFAULT_TARGET_TEMPERATURE,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return VirtualClimateOptionsFlow(config_entry)


class VirtualClimateOptionsFlow(config_entries.OptionsFlow):
    """Manage options for Virtual Climate."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        errors: dict[str, str] = {}
        defaults = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            try:
                climate_names = _parse_climate_names(user_input[CONF_CLIMATE_NAMES])
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_CLIMATE_NAMES: ", ".join(climate_names),
                        CONF_INITIAL_CURRENT_TEMPERATURE: float(
                            user_input[CONF_INITIAL_CURRENT_TEMPERATURE]
                        ),
                        CONF_INITIAL_TARGET_TEMPERATURE: float(
                            user_input[CONF_INITIAL_TARGET_TEMPERATURE]
                        ),
                    },
                )
            except ValueError:
                errors[CONF_CLIMATE_NAMES] = "climate_names_required"

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults, include_name=False),
            errors=errors,
        )


def _build_schema(
    defaults: dict[str, Any],
    *,
    include_name: bool = True,
) -> vol.Schema:
    """Build the config flow schema."""
    schema: dict[Any, Any] = {}
    if include_name:
        schema[vol.Required("name", default=defaults.get("name", DEFAULT_ENTRY_NAME))] = str
    schema[
        vol.Required(
            CONF_CLIMATE_NAMES,
            default=defaults.get(CONF_CLIMATE_NAMES, DEFAULT_CLIMATE_NAMES),
        )
    ] = selector.TextSelector(
        selector.TextSelectorConfig(
            type=selector.TextSelectorType.TEXT,
            multiline=False,
        )
    )
    schema[
        vol.Required(
            CONF_INITIAL_CURRENT_TEMPERATURE,
            default=defaults.get(
                CONF_INITIAL_CURRENT_TEMPERATURE,
                DEFAULT_CURRENT_TEMPERATURE,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=40,
            step=0.5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="°C",
        )
    )
    schema[
        vol.Required(
            CONF_INITIAL_TARGET_TEMPERATURE,
            default=defaults.get(
                CONF_INITIAL_TARGET_TEMPERATURE,
                DEFAULT_TARGET_TEMPERATURE,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=35,
            step=0.5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="°C",
        )
    )
    return vol.Schema(schema)
