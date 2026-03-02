"""Data update coordinator for Skylink Orbit garage doors."""

from __future__ import annotations

import logging
from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DoorDevice, OrbitApiError, OrbitAuthError, OrbitConnectionError, OrbitHomeAPI
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

SkyLinkOrbitConfigEntry: TypeAlias = "ConfigEntry[SkyLinkOrbitData]"


class SkyLinkOrbitData:
    """Runtime data stored in hass.data for a config entry."""

    def __init__(self, api: OrbitHomeAPI, coordinator: SkyLinkOrbitCoordinator) -> None:
        self.api = api
        self.coordinator = coordinator


class SkyLinkOrbitCoordinator(DataUpdateCoordinator[dict[str, DoorDevice]]):
    """Coordinator that manages MQTT connection and door state updates."""

    config_entry: SkyLinkOrbitConfigEntry

    def __init__(self, hass: HomeAssistant, api: OrbitHomeAPI) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api
        self._devices: dict[str, DoorDevice] = {}
        self._mqtt_started = False

    async def _async_update_data(self) -> dict[str, DoorDevice]:
        """Fetch all door states."""
        try:
            # First update: build device list from config and connect MQTT
            if not self._devices:
                devices = self.api.get_devices()
                self._devices = {d.device_id: d for d in devices}
                _LOGGER.info(
                    "Loaded %d door(s): %s",
                    len(self._devices), list(self._devices.keys()),
                )

            # Connect MQTT once (for door control and state)
            if not self._mqtt_started:
                try:
                    await self.api.connect_mqtt()
                    self._mqtt_started = True
                except Exception as err:
                    _LOGGER.warning("MQTT connection failed: %s", err)

            # Try to get state for each device via MQTT
            if self._mqtt_started:
                for hub_id, device in self._devices.items():
                    try:
                        state = await self.api.get_door_state(hub_id)
                        device.state = state
                    except Exception:
                        _LOGGER.debug("Could not get state for %s", hub_id)

        except OrbitAuthError as err:
            raise ConfigEntryAuthFailed(
                "Authentication expired, please re-enter credentials"
            ) from err
        except OrbitConnectionError as err:
            raise UpdateFailed(f"Cannot reach Skylink cloud: {err}") from err
        except OrbitApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

        return self._devices
