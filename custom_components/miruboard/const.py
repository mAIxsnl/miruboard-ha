"""Constants for the Miruboard integration."""

DOMAIN = "miruboard"
PLATFORMS = ["sensor", "calendar"]

# Config keys
CONF_SUPABASE_URL = "supabase_url"
CONF_SUPABASE_KEY = "supabase_key"
CONF_GOOGLE_MAPS_KEY = "google_maps_key"
CONF_CRYPTO_COINS = "crypto_coins"
CONF_CRYPTO_CURRENCY = "crypto_currency"
CONF_TRAVEL_ROUTES = "travel_routes"
CONF_TRAVEL_ORIGIN = "travel_origin"
CONF_TRAVEL_PROVIDER = "travel_provider"
CONF_RSS_FEEDS = "rss_feeds"
CONF_CALENDAR_SOURCES = "calendar_sources"

# Defaults
DEFAULT_CRYPTO_COINS = ["bitcoin", "ethereum", "ripple", "solana", "cardano"]
DEFAULT_CRYPTO_CURRENCY = "eur"
DEFAULT_SCAN_INTERVAL_CRYPTO = 60  # seconds
DEFAULT_SCAN_INTERVAL_TRAVEL = 300
DEFAULT_SCAN_INTERVAL_RSS = 600
DEFAULT_SCAN_INTERVAL_CALENDAR = 900

# API endpoints
COINGECKO_API = "https://api.coingecko.com/api/v3"
OSRM_API = "https://router.project-osrm.org"
NOMINATIM_API = "https://nominatim.openstreetmap.org"

# CoinGecko symbol mapping
SYMBOL_TO_COINGECKO = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
    "ADA": "cardano",
    "SOL": "solana",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "BNB": "binancecoin",
    "DOGE": "dogecoin",
    "LTC": "litecoin",
    "TRX": "tron",
    "XLM": "stellar",
}
