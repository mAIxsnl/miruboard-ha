# Miruboard HA Integration — Installatie

## Wat je krijgt

| Widget | HA Entity Type | Data Source |
|--------|---------------|-------------|
| **Crypto** | `sensor` per coin | CoinGecko (gratis, geen key) |
| **Reistijden** | `sensor` per route | OSRM + Nominatim (gratis) |
| **RSS Nieuws** | `sensor` | Elke RSS/Atom feed |
| **Agenda** | `calendar` | ICS/iCal URLs (iCloud, BasisOnline, etc.) |

## Lovelace Cards

| Card | Type | Beschrijving |
|------|------|-------------|
| `miruboard-crypto-card` | Individueel | Crypto prijzen met 24h change |
| `miruboard-travel-card` | Individueel | Reistijden met verkeersindicator |
| `miruboard-rss-card` | Individueel | Nieuws carousel met auto-rotatie |
| `miruboard-dashboard-card` | Gecombineerd | Alles in één card |

---

## Stap 1: Custom Component installeren

### Via HACS (aanbevolen)

1. Open HACS in Home Assistant
2. Ga naar **Integrations** → **drie puntjes** → **Custom repositories**
3. Voeg toe: `https://github.com/mAIxsnl/miruboard-ha` (categorie: Integration)
4. Zoek "Miruboard" en installeer
5. Herstart Home Assistant

### Handmatig

1. Kopieer `custom_components/miruboard/` naar je HA config:
   ```bash
   # Via Samba share of SSH add-on
   scp -r custom_components/miruboard/ /config/custom_components/
   ```
2. Herstart Home Assistant

## Stap 2: Integratie configureren (Supabase auto-import)

1. Ga naar **Settings** → **Devices & Services** → **Add Integration**
2. Zoek "Miruboard"
3. Vul je **Supabase URL** en **Anon Key** in — de integratie importeert automatisch:
   - Crypto coins (BTC, ETH, XRP)
   - Reistijden (Molenwal → Jenaplan, Shift2) + Google Maps API key
   - RSS feeds (NU.nl)
   - Agenda's (iCloud, BasisOnline, SocialSchools)
4. Bevestig de gevonden widgets → klaar!

**Je Supabase gegevens** (staan in Miruboard `.env.local`):
- URL: `https://brcefchxsumyyoilaoep.supabase.co`
- Key: de `SUPABASE_ANON_KEY` waarde

### Re-sync na wijzigingen in Miruboard

Als je widgets aanpast in Miruboard admin, sync je HA via:
**Settings** → **Devices & Services** → **Miruboard** → **Configure** → **Re-sync from Miruboard** ✓

## Stap 3: Lovelace Card installeren

1. Kopieer `www/miruboard-card.js` naar `/config/www/`:
   ```bash
   scp www/miruboard-card.js /config/www/
   ```
2. Voeg resource toe in HA:
   - Ga naar **Settings** → **Dashboards** → **drie puntjes** → **Resources**
   - Klik **Add Resource**
   - URL: `/local/miruboard-card.js`
   - Type: **JavaScript Module**

## Stap 4: Cards toevoegen aan dashboard

### Optie A: Gecombineerde dashboard card

```yaml
type: custom:miruboard-dashboard-card
title: Miruboard
crypto_entities:
  - sensor.miruboard_bitcoin
  - sensor.miruboard_ethereum
  - sensor.miruboard_solana
travel_entities:
  - sensor.miruboard_werk
  - sensor.miruboard_school
rss_entity: sensor.miruboard_nieuws
```

### Optie B: Individuele cards

```yaml
# Crypto
type: custom:miruboard-crypto-card
title: Crypto
entities:
  - sensor.miruboard_bitcoin
  - sensor.miruboard_ethereum
  - sensor.miruboard_ripple
  - sensor.miruboard_solana
  - sensor.miruboard_cardano

---
# Reistijden
type: custom:miruboard-travel-card
title: Reistijden
entities:
  - sensor.miruboard_werk
  - sensor.miruboard_school

---
# Nieuws
type: custom:miruboard-rss-card
entity: sensor.miruboard_nieuws
title: Nieuws
rotate_seconds: 15
max_items: 5
```

### Optie C: Via HA card picker

De cards verschijnen automatisch in de card picker onder "Custom Cards" als je een nieuwe card toevoegt.

---

## Entities die worden aangemaakt

Na installatie heb je deze entities:

| Entity ID | Type | Beschrijving |
|-----------|------|-------------|
| `sensor.miruboard_bitcoin` | Crypto | BTC prijs + 24h change |
| `sensor.miruboard_ethereum` | Crypto | ETH prijs + 24h change |
| `sensor.miruboard_<coin>` | Crypto | Per geconfigureerde coin |
| `sensor.miruboard_<route>` | Travel | Reistijd in minuten |
| `sensor.miruboard_nieuws` | RSS | Laatste headline + items als attributen |
| `calendar.miruboard_agenda` | Calendar | Geaggregeerde agenda |

## Update-intervallen

| Widget | Interval | Reden |
|--------|----------|-------|
| Crypto | 60s | CoinGecko rate limit |
| Reistijden | 5 min | OSRM/Nominatim rate limits |
| RSS | 10 min | Feeds updaten niet vaker |
| Agenda | 15 min | ICS fetch overhead |

## Aanpassen via Options

Na installatie kun je de configuratie wijzigen via:
**Settings** → **Devices & Services** → **Miruboard** → **Configure**
