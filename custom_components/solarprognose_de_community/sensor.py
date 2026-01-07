import logging
from datetime import timedelta
from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class SolarSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Any], Any] = None
    attr_fn: Callable[[Any], dict[str, Any]] = None

SENSOR_TYPES: tuple[SolarSensorEntityDescription, ...] = (
    SolarSensorEntityDescription(
        key="today_total",
        translation_key="today_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        # Summiert alle Werte des aktuellen Kalendertages
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date()), 2),
    ),
    SolarSensorEntityDescription(
        key="tomorrow_total",
        translation_key="tomorrow_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == (dt_util.now().date() + timedelta(days=1))), 2),
    ),
    SolarSensorEntityDescription(
        key="rest_day",
        translation_key="rest_day",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt >= dt_util.now() and dt.date() == dt_util.now().date()), 2),
    ),
    SolarSensorEntityDescription(
        key="current_hour",
        translation_key="current_hour",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda coord: int((coord.data or {}).get(
            dt_util.now().replace(minute=0, second=0, microsecond=0), 0) * 1000),
    ),
    SolarSensorEntityDescription(
        key="next_hour",
        translation_key="next_hour",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda coord: int((coord.data or {}).get(
            (dt_util.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0), 0) * 1000),
    ),
    SolarSensorEntityDescription(
        key="peak_power_today",
        translation_key="peak_power_today",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int(max([val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date()] or [0]) * 1000),
    ),
    SolarSensorEntityDescription(
        key="peak_time_today",
        translation_key="peak_time_today",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: (
            max([(val, dt) for dt, val in (coord.data or {}).items() if dt.date() == dt_util.now().date()] or [(0, None)])[1]
        ),
    ),
    SolarSensorEntityDescription(
        key="peak_power_tomorrow",
        translation_key="peak_power_tomorrow",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coord: int(max([val for dt, val in (coord.data or {}).items() 
            if dt.date() == (dt_util.now().date() + timedelta(days=1))] or [0]) * 1000),
    ),
    SolarSensorEntityDescription(
        key="forecast",
        translation_key="forecast",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        # Erzeugt den gleitenden Prognose-Wert für das HA-Energie-Dashboard
        value_fn=lambda coord: round(sum(val for dt, val in (coord.data or {}).items() 
            if dt.date() == dt_util.now().date() and dt <= dt_util.now()), 2),
        attr_fn=lambda coord: {
            "forecast": [{"datetime": dt.isoformat(), "energy": val} 
                         for dt, val in sorted((coord.data or {}).items())],
            "integrated_forecast": True
        }
    ),
    SolarSensorEntityDescription(
        key="peak_time_tomorrow",
        translation_key="peak_time_tomorrow",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coord: (
            max([(val, dt) for dt, val in (coord.data or {}).items() 
                if dt.date() == (dt_util.now().date() + timedelta(days=1))] or [(0, None)])[1]
        ),
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
    SolarSensorEntityDescription(key="next_update", translation_key="next_update", device_class=SensorDeviceClass.TIMESTAMP, value_fn=lambda coord: coord.next_api_request),
    SolarSensorEntityDescription(key="last_update", translation_key="last_update", device_class=SensorDeviceClass.TIMESTAMP, value_fn=lambda coord: coord.last_api_success),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    custom_name = entry.data.get("name", "Solarprognose")
    async_add_entities(SolarSensor(coordinator, entry, custom_name, desc) for desc in SENSOR_TYPES)

class SolarSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, custom_name, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": custom_name,
            "manufacturer": "Solarprognose.de (Community)",
            "model": "WebAPI v1",
        }

    async def async_added_to_hass(self) -> None:
        """Wird aufgerufen, wenn die Entitaet hinzugefügt wird."""
        await super().async_added_to_hass()
        
        # Verhindert, dass der api_count nach einem HA-Neustart bei 0 beginnt, 
        # falls heute bereits Abfragen stattgefunden haben.
        if self.entity_description.key == "api_count":
            last_state = await self.async_get_last_state()
            if last_state and last_state.state not in (None, "unknown", "unavailable"):
                try:
                    restored_count = int(last_state.state)
                    if restored_count > self.coordinator.api_count_today:
                        self.coordinator.api_count_today = restored_count
                except ValueError:
                    _LOGGER.error("Konnte API Count nicht wiederherstellen: %s", last_state.state)

    @property
    def native_value(self):
        """Gibt den aktuellen Status des Sensors zurück."""
        # Verhindert Fehlermeldungen im Log, wenn noch keine Daten vom Coordinator vorliegen
        if not self.coordinator.data and self.entity_description.key not in ["api_count", "api_status"]:
            return None
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self):
        """Gibt zusätzliche Attribute zurück (z.B. Forecast-Liste)."""
        return self.entity_description.attr_fn(self.coordinator) if self.entity_description.attr_fn else None