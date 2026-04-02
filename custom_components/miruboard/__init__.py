"""Miruboard integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CARD_JS = Path(__file__).parent / "miruboard-card.js"
CARD_URL = "/miruboard/miruboard-card.js"

type MiruboardConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Miruboard component."""
    # Register static path for the Lovelace card JS
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_JS), cache_headers=True)]
    )

    # Register as a Lovelace resource
    await _register_card_resource(hass)

    return True


async def _register_card_resource(hass: HomeAssistant) -> None:
    """Register the Miruboard card as a Lovelace resource if not already present."""
    # Use the lovelace resources collection
    try:
        resources = hass.data.get("lovelace", {}).get("resources")
        if resources is not None:
            # Check if already registered
            for item in resources.async_items():
                if "miruboard" in item.get("url", ""):
                    return
            # Add new resource
            await resources.async_create_item(
                {"res_type": "module", "url": CARD_URL}
            )
            _LOGGER.info("Registered Miruboard card as Lovelace resource: %s", CARD_URL)
        else:
            _LOGGER.debug("Lovelace resources not available, card must be added manually")
    except Exception:
        _LOGGER.debug("Could not auto-register Lovelace resource, add manually: %s", CARD_URL)


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

    # Always set up sensor (crypto is default on)
    if Platform.SENSOR not in platforms:
        platforms.append(Platform.SENSOR)

    # Deduplicate
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
