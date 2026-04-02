"""Sensor platform for Miruboard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CRYPTO_COINS,
    CONF_CRYPTO_CURRENCY,
    DEFAULT_CRYPTO_COINS,
    DEFAULT_CRYPTO_CURRENCY,
    DOMAIN,
)
from .coordinator import CryptoCoordinator, RssCoordinator, TravelTimeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Miruboard sensors from a config entry."""
    config_data = entry.data
    entities: list[SensorEntity] = []

    # Crypto sensors
    if config_data.get("crypto_enabled", True):
        crypto_coordinator = CryptoCoordinator(hass, config_data)
        await crypto_coordinator.async_config_entry_first_refresh()

        coins = config_data.get(CONF_CRYPTO_COINS, DEFAULT_CRYPTO_COINS)
        currency = config_data.get(CONF_CRYPTO_CURRENCY, DEFAULT_CRYPTO_CURRENCY)

        for coin in coins:
            coin_lower = coin.lower().strip()
            # Resolve to CoinGecko ID
            from .coordinator import SYMBOL_TO_ID

            coin_id = SYMBOL_TO_ID.get(coin_lower, coin_lower)
            entities.append(
                MiruboardCryptoSensor(
                    crypto_coordinator, entry, coin_id, coin, currency
                )
            )

    # Travel time sensors
    if config_data.get("travel_enabled"):
        travel_coordinator = TravelTimeCoordinator(hass, config_data)
        await travel_coordinator.async_config_entry_first_refresh()

        routes = config_data.get("travel_routes", [])
        for route in routes:
            name = route.get("name", "Route")
            entities.append(
                MiruboardTravelTimeSensor(travel_coordinator, entry, name, route)
            )

    # RSS sensor
    if config_data.get("rss_enabled"):
        rss_coordinator = RssCoordinator(hass, config_data)
        await rss_coordinator.async_config_entry_first_refresh()
        entities.append(MiruboardRssSensor(rss_coordinator, entry))

    async_add_entities(entities)


class MiruboardCryptoSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a cryptocurrency price."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: CryptoCoordinator,
        entry: ConfigEntry,
        coin_id: str,
        coin_name: str,
        currency: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coin_id = coin_id
        self._coin_name = coin_name
        self._currency = currency
        self._attr_unique_id = f"{entry.entry_id}_crypto_{coin_id}"
        self._attr_name = f"Miruboard {coin_name.upper()}"
        self._attr_icon = "mdi:currency-btc" if "bitcoin" in coin_id else "mdi:chart-line"

        currency_map = {
            "eur": "EUR",
            "usd": "USD",
            "gbp": "GBP",
        }
        self._attr_native_unit_of_measurement = currency_map.get(currency, currency.upper())
        self._attr_device_class = SensorDeviceClass.MONETARY

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Miruboard",
            "manufacturer": "Miruboard",
            "model": "Dashboard",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if not self.coordinator.data:
            return None
        coin_data = self.coordinator.data.get(self._coin_id, {})
        return coin_data.get("price")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        coin_data = self.coordinator.data.get(self._coin_id, {})
        return {
            "change_24h": coin_data.get("change_24h", 0),
            "market_cap": coin_data.get("market_cap", 0),
            "coin_id": self._coin_id,
            "currency": self._currency,
        }


class MiruboardTravelTimeSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a travel route duration."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:car-clock"
    _attr_device_class = SensorDeviceClass.DURATION

    def __init__(
        self,
        coordinator: TravelTimeCoordinator,
        entry: ConfigEntry,
        route_name: str,
        route_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._route_name = route_name
        self._route_config = route_config
        safe_name = route_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{entry.entry_id}_travel_{safe_name}"
        self._attr_name = f"Miruboard {route_name}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Miruboard",
            "manufacturer": "Miruboard",
            "model": "Dashboard",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> int | None:
        """Return the travel duration in minutes."""
        if not self.coordinator.data:
            return None
        route_data = self.coordinator.data.get(self._route_name, {})
        return route_data.get("duration")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        route_data = self.coordinator.data.get(self._route_name, {})
        return {
            "origin": route_data.get("origin", ""),
            "destination": route_data.get("destination", ""),
            "traffic": route_data.get("traffic", "unknown"),
            "status": route_data.get("status", "unknown"),
        }


class MiruboardRssSensor(CoordinatorEntity, SensorEntity):
    """Sensor for RSS feed aggregation."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:rss"

    def __init__(
        self,
        coordinator: RssCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_rss"
        self._attr_name = "Miruboard Nieuws"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Miruboard",
            "manufacturer": "Miruboard",
            "model": "Dashboard",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> str | None:
        """Return the latest headline."""
        if not self.coordinator.data:
            return None
        items = self.coordinator.data.get("items", [])
        if items:
            return items[0].get("title", "No news")
        return "No news"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all RSS items as attributes."""
        if not self.coordinator.data:
            return {}
        items = self.coordinator.data.get("items", [])
        return {
            "items": items[:10],  # Limit for HA attribute size
            "item_count": len(items),
            "feed_count": self.coordinator.data.get("feed_count", 0),
            "latest_title": items[0]["title"] if items else None,
            "latest_source": items[0]["source"] if items else None,
            "latest_link": items[0]["link"] if items else None,
        }
