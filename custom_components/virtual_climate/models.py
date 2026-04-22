"""Runtime models for Virtual Climate."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.climate import HVACMode


@dataclass(slots=True)
class VirtualClimateState:
    """Mutable runtime state for one virtual climate entity."""

    name: str
    current_temperature: float
    target_temperature: float
    hvac_mode: HVACMode
    available: bool = True
