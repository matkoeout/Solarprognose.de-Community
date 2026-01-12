import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SolarPrognoseCoordinator(DataUpdateCoordinator):
    """Zentrale Instanz zum Abrufen und Aufbereiten der Prognosedaten."""
    
    def __init__(self, hass, api_url=None, api_key=None):
        # Falls keine fertige URL geliefert wurde, bauen wir sie aus dem API-Key zusammen
        self.api_url = api_url or (
            "https://www.solarprognose.de/web/solarprediction/api/v1"
            f"?access-token={api_key}&type=hourly&_format=json"
        )
        
        # 150 Minuten Intervall entspricht ca. 10 Abfragen/Tag (Sicherheitspuffer für das 12er Limit)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=150))
        
        self.api_status = None
        self.api_message = ""
        self.next_api_request = None
        self.last_api_success = None
        self.api_count_today = 0
        self.last_reset_day = dt_util.now().date()

    async def _async_update_data(self):
        """Daten von der API abrufen und verarbeiten."""
        now = dt_util.now()
        
        # API-Zähler bei Datumswechsel zuruecksetzen
        if now.date() > self.last_reset_day:
            self.api_count_today = 0
            self.last_reset_day = now.date()
            
        try:
            async with async_timeout.timeout(20):
                session = async_get_clientsession(self.hass)
                async with session.get(self.api_url) as response:
                    res = await response.json()
                    self.api_status = res.get("status")
                    self.api_message = res.get("message", "")
                    
                    # Status 0 bedeutet bei Solarprognose.de "Erfolg"
                    if self.api_status != 0:
                        _LOGGER.error("Solarprognose API Fehler: %s", self.api_message)
                        return self.data or {}

                    self.last_api_success = now
                    
                    # Empfehlung der API für den naechsten optimalen Abrufzeitpunkt speichern
                    if next_req := res.get("preferredNextApiRequestAt"):
                        ts_seconds = int(next_req.get("epochTimeUtc", 0))
                        if ts_seconds > 0:
                            self.next_api_request = dt_util.utc_from_timestamp(ts_seconds)
                    
                    # Rohdaten (Timestamps) in lokale Datetime-Objekte umwandeln
                    processed_data = {}
                    for ts, v in res.get("data", {}).items():
                        local_dt = dt_util.as_local(dt_util.utc_from_timestamp(int(ts)))
                        processed_data[local_dt] = float(v[0])
                        
                    self.api_count_today += 1
                    return processed_data

        except Exception as err:
            raise UpdateFailed(f"Verbindungsfehler zur API: {err}") from err