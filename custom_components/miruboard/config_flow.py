"""Config flow for Miruboard integration — imports config from Miruboard Supabase."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_CALENDAR_SOURCES,
    CONF_CRYPTO_COINS,
    CONF_CRYPTO_CURRENCY,
    CONF_GOOGLE_MAPS_KEY,
    CONF_RSS_FEEDS,
    CONF_SUPABASE_KEY,
    CONF_SUPABASE_URL,
    CONF_TRAVEL_ORIGIN,
    CONF_TRAVEL_PROVIDER,
    CONF_TRAVEL_ROUTES,
    DEFAULT_CRYPTO_CURRENCY,
    DOMAIN,
    SYMBOL_TO_COINGECKO,
)

_LOGGER = logging.getLogger(__name__)


async def _fetch_supabase_config(
    url: str, key: str
) -> dict[str, Any]:
    """Fetch widget + settings config from Miruboard's Supabase."""
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    result: dict[str, Any] = {"widgets": [], "settings": {}}

    async with aiohttp.ClientSession() as session:
        # Fetch widgets
        async with session.get(
            f"{url}/rest/v1/widgets?select=*",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                result["widgets"] = await resp.json()
            else:
                _LOGGER.warning("Supabase widgets fetch: %s", resp.status)

        # Fetch settings
        async with session.get(
            f"{url}/rest/v1/settings?id=eq.dashboard-settings&select=payload",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                rows = await resp.json()
                if rows:
                    result["settings"] = rows[0].get("payload", {})

    return result


def _extract_config_from_widgets(
    widgets: list[dict], settings: dict
) -> dict[str, Any]:
    """Parse Miruboard widget configs into HA config entry data."""
    data: dict[str, Any] = {"name": "Miruboard"}

    for widget in widgets:
        if not widget.get("enabled", False):
            continue

        wtype = widget.get("type", "")
        ws = widget.get("settings", {})

        if wtype == "crypto":
            data["crypto_enabled"] = True
            symbols = ws.get("symbols", [])
            # Convert BTC/ETH symbols to CoinGecko IDs
            data[CONF_CRYPTO_COINS] = [
                SYMBOL_TO_COINGECKO.get(s.upper(), s.lower()) for s in symbols
            ]
            data[CONF_CRYPTO_CURRENCY] = DEFAULT_CRYPTO_CURRENCY

        elif wtype == "traveltime":
            data["travel_enabled"] = True
            origin = ws.get("origin", "")
            destinations = ws.get("destinations", [])
            # Also check single destination
            single_dest = ws.get("destination", "")
            if single_dest and single_dest not in destinations:
                destinations = [single_dest] + destinations

            data[CONF_TRAVEL_ORIGIN] = origin
            data[CONF_TRAVEL_PROVIDER] = ws.get("provider", "osrm")
            data[CONF_TRAVEL_ROUTES] = [
                {"name": dest.split(",")[0].strip(), "origin": origin, "destination": dest}
                for dest in destinations
            ]

        elif wtype == "rss":
            data["rss_enabled"] = True
            sources = ws.get("sources", [])
            data[CONF_RSS_FEEDS] = [
                s["url"] for s in sources if s.get("enabled", True) and s.get("url")
            ]

        elif wtype == "calendar":
            data["calendar_enabled"] = True
            sources = ws.get("sources", [])
            data[CONF_CALENDAR_SOURCES] = [
                s["url"] for s in sources if s.get("enabled", True) and s.get("url")
            ]

    # Extract API keys from settings
    production = settings.get("production", {})
    if production.get("googleMapsApiKey"):
        data[CONF_GOOGLE_MAPS_KEY] = production["googleMapsApiKey"]

    return data


class MiruboardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Miruboard."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Enter Supabase credentials to import from Miruboard."""
        errors: dict[str, str] = {}

        if user_input is not None:
            supabase_url = user_input[CONF_SUPABASE_URL].rstrip("/")
            supabase_key = user_input[CONF_SUPABASE_KEY]

            try:
                config = await _fetch_supabase_config(supabase_url, supabase_key)
                widgets = config.get("widgets", [])
                settings = config.get("settings", {})

                if not widgets:
                    errors["base"] = "no_widgets"
                else:
                    # Parse Miruboard config into HA config
                    self._data = _extract_config_from_widgets(widgets, settings)
                    self._data[CONF_SUPABASE_URL] = supabase_url
                    self._data[CONF_SUPABASE_KEY] = supabase_key

                    # Count what we found
                    found = []
                    if self._data.get("crypto_enabled"):
                        coins = self._data.get(CONF_CRYPTO_COINS, [])
                        found.append(f"{len(coins)} crypto")
                    if self._data.get("travel_enabled"):
                        routes = self._data.get(CONF_TRAVEL_ROUTES, [])
                        found.append(f"{len(routes)} reistijden")
                    if self._data.get("rss_enabled"):
                        feeds = self._data.get(CONF_RSS_FEEDS, [])
                        found.append(f"{len(feeds)} RSS feeds")
                    if self._data.get("calendar_enabled"):
                        cals = self._data.get(CONF_CALENDAR_SOURCES, [])
                        found.append(f"{len(cals)} agenda's")

                    _LOGGER.info(
                        "Miruboard import: %s widgets, found: %s",
                        len(widgets),
                        ", ".join(found),
                    )

                    return await self.async_step_confirm()

            except aiohttp.ClientError as err:
                _LOGGER.error("Supabase connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Miruboard import")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SUPABASE_URL,
                        default="https://brcefchxsumyyoilaoep.supabase.co",
                    ): str,
                    vol.Required(CONF_SUPABASE_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "description": "Voer je Miruboard Supabase URL en anon key in om alle widgets automatisch te importeren."
            },
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Show what was found and confirm."""
        if user_input is not None:
            return self.async_create_entry(
                title="Miruboard",
                data=self._data,
            )

        # Build description of what we found
        parts = []
        if self._data.get("crypto_enabled"):
            coins = self._data.get(CONF_CRYPTO_COINS, [])
            parts.append(f"Crypto: {', '.join(c.upper() for c in coins)}")
        if self._data.get("travel_enabled"):
            routes = self._data.get(CONF_TRAVEL_ROUTES, [])
            route_names = [r["name"] for r in routes]
            parts.append(f"Reistijden: {', '.join(route_names)}")
        if self._data.get("rss_enabled"):
            parts.append(f"RSS: {len(self._data.get(CONF_RSS_FEEDS, []))} feed(s)")
        if self._data.get("calendar_enabled"):
            parts.append(
                f"Agenda: {len(self._data.get(CONF_CALENDAR_SOURCES, []))} bron(nen)"
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "summary": "\n".join(parts) if parts else "Geen widgets gevonden",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> MiruboardOptionsFlow:
        """Get the options flow."""
        return MiruboardOptionsFlow(config_entry)


class MiruboardOptionsFlow(OptionsFlow):
    """Handle options — re-sync from Supabase or manual edit."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            if user_input.get("resync"):
                # Re-import from Supabase
                url = self._config_entry.data.get(CONF_SUPABASE_URL, "")
                key = self._config_entry.data.get(CONF_SUPABASE_KEY, "")
                if url and key:
                    try:
                        config = await _fetch_supabase_config(url, key)
                        new_data = _extract_config_from_widgets(
                            config.get("widgets", []),
                            config.get("settings", {}),
                        )
                        new_data[CONF_SUPABASE_URL] = url
                        new_data[CONF_SUPABASE_KEY] = key
                        self.hass.config_entries.async_update_entry(
                            self._config_entry, data=new_data
                        )
                        _LOGGER.info("Miruboard config re-synced from Supabase")
                    except Exception:
                        _LOGGER.exception("Re-sync from Supabase failed")
            else:
                # Manual overrides
                coins_str = user_input.get("crypto_coins", "")
                coins = [c.strip() for c in coins_str.split(",") if c.strip()]

                feeds_str = user_input.get("rss_feeds", "")
                feeds = [f.strip() for f in feeds_str.split(",") if f.strip()]

                cal_str = user_input.get("calendar_sources", "")
                cal_sources = [s.strip() for s in cal_str.split(",") if s.strip()]

                routes = self._config_entry.data.get(CONF_TRAVEL_ROUTES, [])
                routes_str = user_input.get("travel_routes", "[]")
                try:
                    routes = json.loads(routes_str)
                except json.JSONDecodeError:
                    pass

                new_data = {
                    **self._config_entry.data,
                    CONF_CRYPTO_COINS: coins,
                    CONF_TRAVEL_ROUTES: routes,
                    CONF_RSS_FEEDS: feeds,
                    CONF_CALENDAR_SOURCES: cal_sources,
                }
                self.hass.config_entries.async_update_entry(
                    self._config_entry, data=new_data
                )

            return self.async_create_entry(title="", data={})

        data = self._config_entry.data
        coin_names = data.get(CONF_CRYPTO_COINS, [])
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("resync", default=False): bool,
                    vol.Optional(
                        "crypto_coins",
                        default=",".join(coin_names),
                    ): str,
                    vol.Optional(
                        "travel_routes",
                        default=json.dumps(
                            data.get(CONF_TRAVEL_ROUTES, []), indent=2
                        ),
                    ): str,
                    vol.Optional(
                        "rss_feeds",
                        default=",".join(data.get(CONF_RSS_FEEDS, [])),
                    ): str,
                    vol.Optional(
                        "calendar_sources",
                        default=",".join(data.get(CONF_CALENDAR_SOURCES, [])),
                    ): str,
                }
            ),
        )
