import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SolarPrognoseCoordinator(DataUpdateCoordinator):
    """Zentrale Instanz zum Abrufen der Daten."""
    
    def __init__(self, hass, api_url=None, api_key=None):
        self.api_url = api_url or (
            "https://www.solarprognose.de/web/solarprediction/api/v1"
            f"?access-token={api_key}&type=hourly&_format=json"
        )
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=150))
        self.api_status = None
        self.api_message = ""
        self.next_api_request = None
        self.last_api_success = None
        self.api_count_today = 0
        self.last_reset_day = dt_util.now().date()

    async def _async_update_data(self):
        now = dt_util.now()
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
                    
                    if self.api_status != 0:
                        _LOGGER.error("Solarprognose API Fehler: %s", self.api_message)
                        return self.data or {}

                    self.last_api_success = now
                    if next_req := res.get("preferredNextApiRequestAt"):
                        self.next_api_request = dt_util.as_local(
                            dt_util.utc_from_timestamp(int(next_req["epochTimeUtc"]))
                        )
                    
                    processed_data = {}
                    for ts, v in res.get("data", {}).items():
                        local_dt = dt_util.as_local(dt_util.utc_from_timestamp(int(ts)))
                        processed_data[local_dt] = float(v[0])
                    self.api_count_today += 1
                    return processed_data

        except Exception as err:
            raise UpdateFailed(f"API Fehler: {err}") from err