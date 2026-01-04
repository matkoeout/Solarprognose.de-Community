import logging
import async_timeout
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)
DOMAIN = "solarprognose_de_community"

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    custom_name = entry.data.get("name", "Solarprognose")

    async_add_entities([
        SolarTodaySensor(coordinator, entry, custom_name),
        SolarTomorrowSensor(coordinator, entry, custom_name),
        SolarRestDaySensor(coordinator, entry, custom_name),
        SolarCurrentHourSensor(coordinator, entry, custom_name),
        SolarNextHourSensor(coordinator, entry, custom_name),
        SolarForecastSensor(coordinator, entry, custom_name),
        SolarNextUpdateSensor(coordinator, entry, custom_name),
        SolarLastUpdateSensor(coordinator, entry, custom_name),
        SolarApiCallCounterSensor(coordinator, entry, custom_name),
        SolarStatusSensor(coordinator, entry, custom_name),
    ])

class SolarPrognoseCoordinator(DataUpdateCoordinator):
    """Zentrale Instanz zum Abrufen der Daten."""
    def __init__(self, hass, api_url=None, api_key=None):
        self.api_url = api_url or (
            f"https://www.solarprognose.de/web/solarprediction/api/v1"
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
                    self.api_count_today += 1
                    res = await response.json()
                    self.api_status = res.get("status")
                    self.api_message = res.get("message", "")
                    
                    if self.api_status != 0:
                        return self.data or {}

                    self.last_api_success = now
                    next_req = res.get("preferredNextApiRequestAt")
                    if next_req and "epochTimeUtc" in next_req:
                        self.next_api_request = dt_util.as_local(
                            dt_util.utc_from_timestamp(int(next_req["epochTimeUtc"]))
                        )
                    
                    return {str(ts): [float(v[0])] for ts, v in res.get("data", {}).items()}
        except Exception as err:
            raise UpdateFailed(f"API Fehler: {err}")

class SolarSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    
    def __init__(self, coordinator, entry, custom_name, translation_key):
        super().__init__(coordinator)
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=custom_name,
            manufacturer="Solarprognose.de",
            model="WebAPI v1",
        )

class SolarForecastSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "forecast")

    @property
    def native_value(self):
        if not self.coordinator.data: return 0.0
        now = dt_util.now()
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == now.date() 
                         and dt_util.as_local(dt_util.utc_from_timestamp(int(ts))) <= now), 2)

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data: return {"integrated_forecast": True}
        return {
            "forecast": [{"datetime": dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).isoformat(), "energy": float(v[0])} 
                         for ts, v in sorted(self.coordinator.data.items())],
            "integrated_forecast": True
        }

class SolarApiCallCounterSensor(SolarSensorBase, RestoreEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:api"

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "api_count")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state.isdigit():
            self.coordinator.api_count_today = int(last_state.state)

    @property
    def native_value(self):
        return self.coordinator.api_count_today

class SolarTodaySensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "today_total")

    @property
    def native_value(self):
        today = dt_util.now().date()
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == today), 2)

class SolarTomorrowSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "tomorrow_total")

    @property
    def native_value(self):
        tomorrow = dt_util.now().date() + timedelta(days=1)
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == tomorrow), 2)

class SolarRestDaySensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "rest_day")

    @property
    def native_value(self):
        now = dt_util.now()
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))) >= now 
                         and dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == now.date()), 2)

class SolarCurrentHourSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "current_hour")

    @property
    def native_value(self):
        ts = str(int(dt_util.now().replace(minute=0, second=0, microsecond=0).timestamp()))
        return int(float(self.coordinator.data.get(ts, [0])[0]) * 1000)

class SolarNextHourSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "next_hour")

    @property
    def native_value(self):
        ts = str(int((dt_util.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).timestamp()))
        return int(float(self.coordinator.data.get(ts, [0])[0]) * 1000)

class SolarStatusSensor(SolarSensorBase):
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "api_status")
    @property
    def native_value(self):
        return "OK" if self.coordinator.api_status == 0 else "Fehler"
    @property
    def extra_state_attributes(self):
        return {"api_message": self.coordinator.api_message}

class SolarNextUpdateSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "next_update")
    @property
    def native_value(self):
        return self.coordinator.next_api_request

class SolarLastUpdateSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "last_update")
    @property
    def native_value(self):
        return self.coordinator.last_api_success