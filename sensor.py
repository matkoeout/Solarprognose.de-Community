import logging
import async_timeout
import json
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
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
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)
DOMAIN = "link_solarprognose_de"

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
        SolarPrognoseWeather(coordinator, entry, custom_name),
    ])

class SolarPrognoseCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url=None, api_key=None):
        if api_url:
            self.api_url = api_url
        else:
            self.api_url = (
                "https://www.solarprognose.de/web/solarprediction/api/v1"
                f"?access-token={api_key}&type=hourly&_format=json"
            )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=150),
        )
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
                    res = json.loads(await response.text())
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
                    return res.get("data", {})
        except Exception as err:
            raise UpdateFailed(f"API Fehler: {err}")

class SolarSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, entry, custom_name, suffix):
        super().__init__(coordinator)
        self._attr_name = suffix
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
    _attr_icon = "mdi:chart-bell-curve"

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Prognose")
        self._attr_unique_id = f"{entry.entry_id}_forecast_energy"
        self._last_value = 0.0

    @property
    def native_value(self):
        return self._last_value

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {"integrated_forecast": True}
        forecast_list = []
        today = dt_util.now().date()
        today_total = 0.0
        for ts, v in self.coordinator.data.items():
            dt_local = dt_util.as_local(dt_util.utc_from_timestamp(int(ts)))
            val = float(v[0])
            forecast_list.append({"datetime": dt_local.isoformat(), "value": val})
            if dt_local.date() == today:
                today_total += val
        self._last_value = max(self._last_value, round(today_total, 2))
        return {"forecast": forecast_list, "integrated_forecast": True}

class SolarTodaySensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:solar-power-variant"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Heute Gesamt")
        self._attr_unique_id = f"{entry.entry_id}_today"

    @property
    def native_value(self):
        today = dt_util.now().date()
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == today), 2)

class SolarTomorrowSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:weather-sunny"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Morgen Gesamt")
        self._attr_unique_id = f"{entry.entry_id}_tomorrow"

    @property
    def native_value(self):
        tomorrow = dt_util.now().date() + timedelta(days=1)
        return round(sum(float(v[0]) for ts, v in self.coordinator.data.items() 
                         if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == tomorrow), 2)

class SolarRestDaySensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:sun-clock"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Resttag")
        self._attr_unique_id = f"{entry.entry_id}_rest_day"

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
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Aktuelle Stunde")
        self._attr_unique_id = f"{entry.entry_id}_current_hour"

    @property
    def native_value(self):
        ts = str(int(dt_util.now().replace(minute=0, second=0).timestamp()))
        return int(float(self.coordinator.data.get(ts, [0])[0]) * 1000)

class SolarNextHourSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_icon = "mdi:lightning-bolt-outline"

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Nächste Stunde")
        self._attr_unique_id = f"{entry.entry_id}_next_hour"

    @property
    def native_value(self):
        ts = str(int((dt_util.now() + timedelta(hours=1)).replace(minute=0, second=0).timestamp()))
        return int(float(self.coordinator.data.get(ts, [0])[0]) * 1000)

class SolarStatusSensor(SolarSensorBase):
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "API Status")
        self._attr_unique_id = f"{entry.entry_id}_api_status"

    @property
    def native_value(self):
        return "OK" if self.coordinator.api_status == 0 else "Fehler"

    @property
    def icon(self):
        return "mdi:check-circle" if self.coordinator.api_status == 0 else "mdi:alert-circle"

    @property
    def extra_state_attributes(self):
        return {"api_message": self.coordinator.api_message}

class SolarApiCallCounterSensor(SolarSensorBase, RestoreEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:api"

    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "API Abfragen Heute")
        self._attr_unique_id = f"{entry.entry_id}_api_calls"

    async def async_added_to_hass(self):
        last = await self.async_get_last_state()
        if last and str(last.state).isdigit():
            self.coordinator.api_count_today = int(last.state)

    @property
    def native_value(self):
        return self.coordinator.api_count_today

class SolarNextUpdateSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Nächste Abfragezeit")
        self._attr_unique_id = f"{entry.entry_id}_next_update"
    @property
    def native_value(self):
        return self.coordinator.next_api_request

class SolarLastUpdateSensor(SolarSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator, entry, name, "Letzte Abfrage")
        self._attr_unique_id = f"{entry.entry_id}_last_update"
    @property
    def native_value(self):
        return self.coordinator.last_api_success

class SolarPrognoseWeather(CoordinatorEntity, WeatherEntity):
    _attr_has_entity_name = True
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
    _attr_condition = "sunny"
    def __init__(self, coordinator, entry, name):
        super().__init__(coordinator)
        self._attr_name = f"{name} Forecast"
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
        )
    async def async_forecast_hourly(self) -> list[Forecast]:
        if not self.coordinator.data:
            return []
        return [
            {
                "datetime": dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).isoformat(),
                "native_energy": float(v[0]),
                "condition": "sunny",
            }
            for ts, v in self.coordinator.data.items()
        ]