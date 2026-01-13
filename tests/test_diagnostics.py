from unittest.mock import MagicMock
from custom_components.solarprognose_de_community.diagnostics import async_get_config_entry_diagnostics
from custom_components.solarprognose_de_community.const import DOMAIN
import pytest

async def test_diagnostics(hass):
    """Testet die Maskierung der API-Keys in den Diagnose-Daten."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {"api_key": "geheim", "name": "Test"}
    # Wir simulieren die as_dict() Methode, die oft intern genutzt wird
    entry.as_dict.return_value = {"data": entry.data, "title": "Test Anlage"}
    
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"forecast": "some_data"}
    hass.data[DOMAIN] = {entry.entry_id: {"coordinator": mock_coordinator}}
    
    result = await async_get_config_entry_diagnostics(hass, entry)
    
    # Wir suchen rekursiv nach dem api_key im result
    def find_key(data, target_key):
        if target_key in data:
            return data[target_key]
        for v in data.values():
            if isinstance(v, dict):
                res = find_key(v, target_key)
                if res: return res
        return None

    api_key_value = find_key(result, "api_key")
    assert api_key_value == "**REDACTED**"