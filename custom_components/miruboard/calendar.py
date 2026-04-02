"""Calendar platform for Miruboard integration — one entity per source with color."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_CALENDAR_SOURCES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Miruboard calendars from config entry — one per source."""
    config_data = entry.data

    if not config_data.get("calendar_enabled"):
        return

    sources = config_data.get(CONF_CALENDAR_SOURCES, [])
    if not sources:
        return

    entities = []
    for source in sources:
        if isinstance(source, str):
            source = {"name": "Agenda", "url": source, "color": "#3b82f6"}
        entities.append(MiruboardCalendar(hass, entry, source))

    async_add_entities(entities)


def _make_aware(dt_val: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (default to UTC)."""
    if dt_val.tzinfo is None:
        return dt_val.replace(tzinfo=dt_util.UTC)
    return dt_val


def _parse_ics_events(
    ics_text: str, range_start: datetime, range_end: datetime
) -> list[dict[str, Any]]:
    """Parse ICS text into event dicts — tolerant of malformed feeds."""
    from icalendar import Calendar

    cal = Calendar.from_ical(ics_text)
    events = []

    # Ensure range bounds are timezone-aware
    range_start = _make_aware(range_start)
    range_end = _make_aware(range_end)

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        try:
            dt_start = component.get("DTSTART")
            dt_end = component.get("DTEND")
            if dt_start is None:
                continue

            start = dt_start.dt
            end = dt_end.dt if dt_end else start

            is_all_day = isinstance(start, date) and not isinstance(start, datetime)

            # Normalize to aware datetime for range comparison
            if is_all_day:
                start_cmp = _make_aware(datetime.combine(start, datetime.min.time()))
                end_cmp = _make_aware(datetime.combine(
                    end if isinstance(end, date) and not isinstance(end, datetime) else start,
                    datetime.min.time(),
                ))
            else:
                start_cmp = _make_aware(start)
                end_cmp = _make_aware(end if isinstance(end, datetime) else start)

            # Filter by range
            if start_cmp > range_end or end_cmp < range_start:
                continue

            summary = str(component.get("SUMMARY", "Event"))
            location = str(component.get("LOCATION", "")) or None

            if is_all_day:
                events.append({
                    "start": start,
                    "end": end if isinstance(end, date) and not isinstance(end, datetime) else start + timedelta(days=1),
                    "summary": summary,
                    "location": location,
                })
            else:
                events.append({
                    "start": _make_aware(start),
                    "end": _make_aware(end if isinstance(end, datetime) else start),
                    "summary": summary,
                    "location": location,
                })
        except Exception:
            continue

    events.sort(key=lambda e: _make_aware(e["start"]) if isinstance(e["start"], datetime) else _make_aware(datetime.combine(e["start"], datetime.min.time())))
    return events


class MiruboardCalendar(CalendarEntity):
    """Calendar entity for a single ICS source."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        source: dict[str, str],
    ) -> None:
        """Initialize the calendar."""
        self.hass = hass
        self._source_url = source["url"]
        self._source_name = source.get("name", "Agenda")
        self._source_color = source.get("color", "#3b82f6")
        self._events: list[CalendarEvent] = []

        safe_name = self._source_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{entry.entry_id}_cal_{safe_name}"
        self._attr_name = self._source_name
        self._attr_icon = "mdi:calendar"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Miruboard",
            "manufacturer": "Miruboard",
            "model": "Dashboard",
            "entry_type": "service",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose source color as attribute."""
        return {
            "color": self._source_color,
            "source_name": self._source_name,
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = dt_util.now()
        upcoming = [e for e in self._events if e.end > now]
        if upcoming:
            upcoming.sort(key=lambda e: e.start)
            return upcoming[0]
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events within the requested time range."""
        await self._fetch_events()
        return [
            e
            for e in self._events
            if e.start < end_date and e.end > start_date
        ]

    async def async_update(self) -> None:
        """Update calendar events."""
        await self._fetch_events()

    async def _fetch_events(self) -> None:
        """Fetch and parse ICS calendar using icalendar (tolerant parser)."""
        now = dt_util.now()
        range_end = now + timedelta(days=30)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._source_url,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={"User-Agent": "Miruboard-HA/1.0"},
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.warning(
                            "Calendar fetch failed for %s: %s",
                            self._source_name,
                            resp.status,
                        )
                        return
                    ics_text = await resp.text()
        except aiohttp.ClientError as err:
            _LOGGER.warning("Calendar fetch error for %s: %s", self._source_name, err)
            return

        try:
            raw_events = await self.hass.async_add_executor_job(
                _parse_ics_events, ics_text, now, range_end
            )

            self._events = [
                CalendarEvent(
                    start=ev["start"],
                    end=ev["end"],
                    summary=ev["summary"],
                    location=ev["location"],
                )
                for ev in raw_events
            ]
        except Exception:
            _LOGGER.exception("Failed to parse calendar from %s", self._source_name)
