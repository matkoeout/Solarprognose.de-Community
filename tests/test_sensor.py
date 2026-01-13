import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from homeassistant.util import dt as dt_util
from custom_components.solarprognose_de_community.const import DOMAIN

async def test_sensors_calculation(hass, mock_api_data):
    """Testet, ob die Sensoren die API-Daten korrekt summieren."""
    
    # 1. Zeitpunkte vorbereiten (Heute und Morgen)
    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    tomorrow = now + timedelta(days=1)
    
    # API-Daten simulieren: 2 kWh heute, 3 kWh morgen
    mock_data = {
        now: 2.0,
        tomorrow: 3.0
    }

    # 2. Coordinator mit Mock-Daten fuettern
    with patch("custom_components.solarprognose_de_community.coordinator.SolarPrognoseCoordinator._async_update_data"):
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"name": "Test Anlage"}
        
        from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator
        coordinator = SolarPrognoseCoordinator(hass, api_key="test")
        coordinator.data = mock_data
        
        # In hass.data registrieren, damit sensor.py ihn findet
        hass.data[DOMAIN] = {entry.entry_id: {"coordinator": coordinator}}

        # 3. Sensoren laden
        from custom_components.solarprognose_de_community.sensor import SENSOR_TYPES, SolarSensor
        
        # Test: Heute Gesamt (today_total)
        today_desc = next(s for s in SENSOR_TYPES if s.key == "today_total")
        sensor_today = SolarSensor(coordinator, entry, "Solar", today_desc)
        assert sensor_today.native_value == 2.0

        # Test: Morgen Gesamt (tomorrow_total)
        tomorrow_desc = next(s for s in SENSOR_TYPES if s.key == "tomorrow_total")
        sensor_tomorrow = SolarSensor(coordinator, entry, "Solar", tomorrow_desc)
        assert sensor_tomorrow.native_value == 3.0

        # Test: Aktuelle Stunde in Watt (current_hour)
        # (2.0 kWh * 1000 = 2000 W)
        curr_hour_desc = next(s for s in SENSOR_TYPES if s.key == "current_hour")
        sensor_power = SolarSensor(coordinator, entry, "Solar", curr_hour_desc)
        assert sensor_power.native_value == 2000