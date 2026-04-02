"""Calendar platform for Miruboard integration — one entity per source with color."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
        # Support both old format (plain URL string) and new format (dict with name/url/color)
        if isinstance(source, str):
            source = {"name": "Agenda", "url": source, "color": "#3b82f6"}
        entities.append(MiruboardCalendar(hass, entry, source))

    async_add_entities(entities)


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
        self._attr_unique_id = f"{entry.entry_id}_calendar_{safe_name}"
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
        """Fetch and parse ICS calendar."""
        from ical.calendar_stream import IcsCalendarStream

        now = dt_util.now()
        range_end = now + timedelta(days=30)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self._source_url,
                    timeout=aiohttp.ClientTimeout(total=10),
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
            calendar = await self.hass.async_add_executor_job(
                IcsCalendarStream.calendar_from_ics, ics_text
            )

            events: list[CalendarEvent] = []
            for event in calendar.timeline.included(now, range_end):
                summary = str(event.summary) if event.summary else "Event"
                location = str(event.location) if event.location else None

                start = event.dtstart
                end = event.dtend if event.dtend else event.dtstart

                if not isinstance(start, datetime):
                    start = datetime.combine(start, datetime.min.time())
                    start = dt_util.as_local(start)
                if not isinstance(end, datetime):
                    end = datetime.combine(end, datetime.min.time())
                    end = dt_util.as_local(end)

                events.append(
                    CalendarEvent(
                        start=start,
                        end=end,
                        summary=summary,
                        location=location,
                    )
                )

            events.sort(key=lambda e: e.start)
            self._events = events
        except Exception:
            _LOGGER.exception("Failed to parse calendar from %s", self._source_name)
