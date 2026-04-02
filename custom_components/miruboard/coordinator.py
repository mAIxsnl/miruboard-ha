"""Data update coordinators for Miruboard."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    COINGECKO_API,
    CONF_CRYPTO_COINS,
    CONF_CRYPTO_CURRENCY,
    CONF_GOOGLE_MAPS_KEY,
    CONF_RSS_FEEDS,
    CONF_TRAVEL_ROUTES,
    DEFAULT_CRYPTO_COINS,
    DEFAULT_CRYPTO_CURRENCY,
    DEFAULT_SCAN_INTERVAL_CRYPTO,
    DEFAULT_SCAN_INTERVAL_RSS,
    DEFAULT_SCAN_INTERVAL_TRAVEL,
    DOMAIN,
    NOMINATIM_API,
    OSRM_API,
)

_LOGGER = logging.getLogger(__name__)

# Coin ID mapping (symbol -> CoinGecko ID)
SYMBOL_TO_ID = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "ripple": "ripple",
    "cardano": "cardano",
    "solana": "solana",
    "polkadot": "polkadot",
    "polygon": "matic-network",
    "avalanche": "avalanche-2",
    "chainlink": "chainlink",
    "uniswap": "uniswap",
    "binancecoin": "binancecoin",
    "dogecoin": "dogecoin",
    "litecoin": "litecoin",
    "tron": "tron",
    "stellar": "stellar",
    # Short aliases
    "btc": "bitcoin",
    "eth": "ethereum",
    "xrp": "ripple",
    "ada": "cardano",
    "sol": "solana",
    "dot": "polkadot",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "link": "chainlink",
    "uni": "uniswap",
    "bnb": "binancecoin",
    "doge": "dogecoin",
    "ltc": "litecoin",
    "trx": "tron",
    "xlm": "stellar",
}


class CryptoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch crypto prices from CoinGecko."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_crypto",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_CRYPTO),
        )
        self._coins = config_data.get(CONF_CRYPTO_COINS, DEFAULT_CRYPTO_COINS)
        self._currency = config_data.get(CONF_CRYPTO_CURRENCY, DEFAULT_CRYPTO_CURRENCY)

    def _resolve_ids(self) -> list[str]:
        """Resolve coin names/symbols to CoinGecko IDs."""
        ids = []
        for coin in self._coins:
            coin_lower = coin.lower().strip()
            resolved = SYMBOL_TO_ID.get(coin_lower, coin_lower)
            if resolved not in ids:
                ids.append(resolved)
        return ids

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch crypto data from CoinGecko."""
        ids = self._resolve_ids()
        if not ids:
            return {}

        url = (
            f"{COINGECKO_API}/simple/price"
            f"?ids={','.join(ids)}"
            f"&vs_currencies={self._currency}"
            f"&include_24hr_change=true"
            f"&include_market_cap=true"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"CoinGecko API returned {resp.status}")
                    raw = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching crypto data: {err}") from err

        result = {}
        for coin_id in ids:
            entry = raw.get(coin_id, {})
            price = entry.get(self._currency, 0)
            change = entry.get(f"{self._currency}_24h_change", 0)
            market_cap = entry.get(f"{self._currency}_market_cap", 0)
            result[coin_id] = {
                "price": price,
                "change_24h": round(change, 2) if change else 0,
                "market_cap": market_cap,
                "currency": self._currency,
            }

        return result


class TravelTimeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch travel times via Google Maps or OSRM."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_travel",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_TRAVEL),
        )
        self._routes = config_data.get(CONF_TRAVEL_ROUTES, [])
        self._google_maps_key = config_data.get(CONF_GOOGLE_MAPS_KEY)
        self._geocode_cache: dict[str, tuple[float, float]] = {}

    async def _geocode(
        self, session: aiohttp.ClientSession, address: str
    ) -> tuple[float, float] | None:
        """Geocode an address to coordinates using Nominatim."""
        if address in self._geocode_cache:
            return self._geocode_cache[address]

        url = (
            f"{NOMINATIM_API}/search"
            f"?q={address}"
            f"&format=json&limit=1&countrycodes=nl"
        )
        try:
            async with session.get(
                url,
                headers={"User-Agent": "Miruboard-HA/1.0"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                results = await resp.json()
                if not results:
                    return None
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                self._geocode_cache[address] = (lat, lon)
                return (lat, lon)
        except (aiohttp.ClientError, KeyError, ValueError, IndexError):
            return None

    async def _fetch_osrm_route(
        self,
        session: aiohttp.ClientSession,
        origin: tuple[float, float],
        dest: tuple[float, float],
    ) -> int | None:
        """Fetch route duration from OSRM in minutes."""
        url = (
            f"{OSRM_API}/route/v1/driving/"
            f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
            f"?overview=false"
        )
        try:
            async with session.get(
                url,
                headers={"User-Agent": "Miruboard-HA/1.0"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                duration_sec = data.get("routes", [{}])[0].get("duration", 0)
                return round(duration_sec / 60)
        except (aiohttp.ClientError, KeyError, IndexError):
            return None

    async def _fetch_google_route(
        self,
        session: aiohttp.ClientSession,
        origin: str,
        destination: str,
    ) -> int | None:
        """Fetch route duration from Google Maps Distance Matrix (with traffic)."""
        if not self._google_maps_key:
            return None

        url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origin}"
            f"&destinations={destination}"
            f"&departure_time=now"
            f"&traffic_model=best_guess"
            f"&key={self._google_maps_key}"
        )
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("status") != "OK":
                    return None
                element = data["rows"][0]["elements"][0]
                if element.get("status") != "OK":
                    return None
                # Use duration_in_traffic for real-time, fallback to duration
                seconds = (
                    element.get("duration_in_traffic", {}).get("value")
                    or element.get("duration", {}).get("value", 0)
                )
                return round(seconds / 60)
        except (aiohttp.ClientError, KeyError, IndexError):
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch travel times for all configured routes."""
        if not self._routes:
            return {}

        result = {}
        provider = "Google Maps" if self._google_maps_key else "OSRM"

        async with aiohttp.ClientSession() as session:
            for route in self._routes:
                name = route.get("name", "Route")
                origin_addr = route.get("origin", "")
                dest_addr = route.get("destination", "")

                if not origin_addr or not dest_addr:
                    continue

                duration = None

                # Try Google Maps first (includes real-time traffic)
                if self._google_maps_key:
                    duration = await self._fetch_google_route(
                        session, origin_addr, dest_addr
                    )
                    if duration:
                        provider = "Google Maps"

                # Fallback to OSRM (free, no API key)
                if duration is None:
                    origin = await self._geocode(session, origin_addr)
                    dest = await self._geocode(session, dest_addr)

                    if not origin or not dest:
                        _LOGGER.warning(
                            "Could not geocode route %s: %s -> %s",
                            name, origin_addr, dest_addr,
                        )
                        result[name] = {
                            "duration": None,
                            "origin": origin_addr,
                            "destination": dest_addr,
                            "provider": "failed",
                            "status": "geocode_failed",
                        }
                        continue

                    duration = await self._fetch_osrm_route(session, origin, dest)
                    provider = "OSRM"

                traffic = "green" if duration and duration <= 35 else "red"

                result[name] = {
                    "duration": duration,
                    "origin": origin_addr,
                    "destination": dest_addr,
                    "traffic": traffic,
                    "provider": provider,
                    "status": "ok" if duration else "route_failed",
                }

        return result


class RssCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch RSS feeds."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_rss",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_RSS),
        )
        self._feeds = config_data.get(CONF_RSS_FEEDS, [])

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and parse RSS feeds."""
        import feedparser

        if not self._feeds:
            return {"items": []}

        all_items: list[dict[str, Any]] = []

        async with aiohttp.ClientSession() as session:
            for feed_url in self._feeds:
                try:
                    async with session.get(
                        feed_url,
                        timeout=aiohttp.ClientTimeout(total=8),
                        headers={"User-Agent": "Miruboard-HA/1.0"},
                    ) as resp:
                        if resp.status != 200:
                            continue
                        content = await resp.text()
                except aiohttp.ClientError:
                    _LOGGER.warning("Failed to fetch RSS feed: %s", feed_url)
                    continue

                feed = await self.hass.async_add_executor_job(
                    feedparser.parse, content
                )
                feed_title = feed.feed.get("title", feed_url)

                for entry in feed.entries[:5]:
                    # Extract image from enclosures or media
                    image_url = None
                    for link in entry.get("links", []):
                        if link.get("type", "").startswith("image/"):
                            image_url = link.get("href")
                            break
                    if not image_url:
                        for media in entry.get("media_content", []):
                            if media.get("medium") == "image" or media.get(
                                "type", ""
                            ).startswith("image/"):
                                image_url = media.get("url")
                                break

                    all_items.append(
                        {
                            "title": entry.get("title", "No title"),
                            "summary": entry.get("summary", ""),
                            "published": entry.get("published", ""),
                            "link": entry.get("link", ""),
                            "source": feed_title,
                            "image_url": image_url,
                        }
                    )

        # Sort by date (newest first), limit to 20
        all_items.sort(key=lambda x: x.get("published", ""), reverse=True)
        return {"items": all_items[:20], "feed_count": len(self._feeds)}
