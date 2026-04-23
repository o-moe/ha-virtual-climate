# ha-virtual-climate

`ha-virtual-climate` is a small Home Assistant custom integration that exposes
virtual `climate` entities and paired helper sensors for development, testing,
and UI prototyping.

It is intended for situations where you need realistic thermostat-like entities
without depending on cloud APIs, physical devices, or vendor bridges.

## Features

- UI config flow
- Multiple virtual climate entities from one integration entry
- Adjustable target temperature and HVAC mode
- Paired current-temperature and humidity sensors per virtual climate
- Paired window-contact binary sensor per virtual climate
- Simulated current temperature
- Toggle entity availability for failure-path testing
- HACS-compatible repository structure

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Go to the three-dot menu and choose **Custom repositories**.
3. Add the repository URL and choose type **Integration**.
4. Install `Virtual Climate`.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/virtual_climate` into your Home Assistant
   `custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings > Devices & services**.
2. Add integration **Virtual Climate**.
3. Enter a display name and a comma-separated list of climate names.
4. Finish setup.

## Services

The integration registers helper services:

- `virtual_climate.set_current_temperature`
- `virtual_climate.set_availability`
- `virtual_climate.set_humidity`
- `virtual_climate.set_window_open`

These can be used to simulate changing room conditions or unavailable devices.

## Example uses

- Test custom dashboards against `climate` entities
- Validate automations without touching real thermostats
- Develop integrations such as ClimateRelay against stable local entities

## Development

```bash
uv sync --locked --group dev
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run python -m build
```

## Releases

The repository uses lightweight semantic versioning with:

- manual alpha pre-releases from selected refs
- automatic beta pre-releases from `main`
- manual stable releases from `main`

See [docs/release-policy.md](docs/release-policy.md) for the release rules.
