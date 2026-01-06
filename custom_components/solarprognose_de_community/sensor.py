import logging
import async_timeout
from datetime import timedelta
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "solarprognose_de_community"

@dataclass(frozen=True)
class SolarSensorEntityDescription(SensorEntityDescription):
    """Eigene Beschreibungsklasse für Solar-Sensoren."""
    value_fn: Callable[[Any], Any] = None
    attr_fn: Callable[[Any], dict[str, Any]] = None

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
                        _LOGGER.error("Solarprognose API Fehler: %s", self.api_message)
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

# --- Definition der Sensoren ---
SENSOR_TYPES: tuple[SolarSensorEntityDescription, ...] = (
    SolarSensorEntityDescription(
        key="today_total",
        translation_key="today_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda coord: round(sum(float(v[0]) for ts, v in coord.data.items() 
            if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == dt_util.now().date()), 2),
    ),
    SolarSensorEntityDescription(
        key="tomorrow_total",
        translation_key="tomorrow_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda coord: round(sum(float(v[0]) for ts, v in coord.data.items() 
            if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == (dt_util.now().date() + timedelta(days=1))), 2),
    ),
    SolarSensorEntityDescription(
        key="rest_day",
        translation_key="rest_day",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda coord: round(sum(float(v[0]) for ts, v in coord.data.items() 
            if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))) >= dt_util.now() 
            and dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == dt_util.now().date()), 2),
    ),
    SolarSensorEntityDescription(
        key="current_hour",
        translation_key="current_hour",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int(float(coord.data.get(str(int(dt_util.now().replace(minute=0, second=0, microsecond=0).timestamp())), [0])[0]) * 1000),
    ),
    SolarSensorEntityDescription(
        key="next_hour",
        translation_key="next_hour",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda coord: int(float(coord.data.get(str(int((dt_util.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).timestamp())), [0])[0]) * 1000),
    ),
    SolarSensorEntityDescription(
        key="forecast",
        translation_key="forecast",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda coord: round(sum(float(v[0]) for ts, v in coord.data.items() 
            if dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).date() == dt_util.now().date() 
            and dt_util.as_local(dt_util.utc_from_timestamp(int(ts))) <= dt_util.now()), 2),
        attr_fn=lambda coord: {
            "forecast": [{"datetime": dt_util.as_local(dt_util.utc_from_timestamp(int(ts))).isoformat(), "energy": float(v[0])} 
                         for ts, v in sorted(coord.data.items())],
            "integrated_forecast": True
        }
    ),
    SolarSensorEntityDescription(
        key="api_count",
        translation_key="api_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:api",
        value_fn=lambda coord: coord.api_count_today,
    ),
    SolarSensorEntityDescription(
        key="api_status",
        translation_key="api_status",
        value_fn=lambda coord: "OK" if coord.api_status == 0 else "Fehler",
        attr_fn=lambda coord: {"api_message": coord.api_message},
    ),
    SolarSensorEntityDescription(
        key="next_update",
        translation_key="next_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: coord.next_api_request,
    ),
    SolarSensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: coord.last_api_success,
    ),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    custom_name = entry.data.get("name", "Solarprognose")

    async_add_entities(
        SolarSensor(coordinator, entry, custom_name, description)
        for description in SENSOR_TYPES
    )

class SolarSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Zentrale Sensorklasse für alle Solarprognose-Entitäten."""
    
    entity_description: SolarSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, custom_name, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": custom_name,
            "manufacturer": "Solarprognose.de",
            "model": "WebAPI v1",
        }

    async def async_added_to_hass(self) -> None:
        """Wird aufgerufen, wenn die Entität zu HA hinzugefügt wird."""
        await super().async_added_to_hass()
        
        if self.entity_description.key == "api_count":
            if (last_state := await self.async_get_last_state()) and last_state.state.isdigit():
                self.coordinator.api_count_today = int(last_state.state)

    @property
    def native_value(self):
        """Berechnet den Wert basierend auf der value_fn."""
        if not self.coordinator.data and self.entity_description.key not in ["api_count", "api_status"]:
            return None
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self):
        """Zusätzliche Attribute."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator)
        return None
