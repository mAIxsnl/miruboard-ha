"""Miruboard integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_JS = Path(__file__).parent / "miruboard-card.js"
CARD_URL = "/miruboard/miruboard-card.js"

type MiruboardConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Miruboard component."""
    # Register static path so the Lovelace card JS is served by HA
    try:
        hass.http.register_static_path(CARD_URL, str(CARD_JS), cache_headers=True)
        _LOGGER.info("Registered Miruboard card at %s", CARD_URL)
    except Exception:
        _LOGGER.debug("Could not register static path for card JS")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: MiruboardConfigEntry) -> bool:
    """Set up Miruboard from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    platforms: list[Platform] = []
    if entry.data.get("crypto_enabled", True):
        platforms.append(Platform.SENSOR)
    if entry.data.get("travel_enabled"):
        platforms.append(Platform.SENSOR)
    if entry.data.get("rss_enabled"):
        platforms.append(Platform.SENSOR)
    if entry.data.get("calendar_enabled"):
        platforms.append(Platform.CALENDAR)

    if Platform.SENSOR not in platforms:
        platforms.append(Platform.SENSOR)

    platforms = list(set(platforms))

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MiruboardConfigEntry) -> bool:
    """Unload a config entry."""
    platforms: list[Platform] = []
    if entry.data.get("crypto_enabled", True):
        platforms.append(Platform.SENSOR)
    if entry.data.get("calendar_enabled"):
        platforms.append(Platform.CALENDAR)
    if Platform.SENSOR not in platforms:
        platforms.append(Platform.SENSOR)
    platforms = list(set(platforms))

    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: MiruboardConfigEntry
) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
