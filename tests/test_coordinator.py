from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.solarprognose_de_community.coordinator import SolarPrognoseCoordinator

async def test_coordinator_api_error(hass):
    """Testet das Verhalten bei einem API-Fehler-Status."""
    coordinator = SolarPrognoseCoordinator(hass, api_key="wrong-key")
    error_data = {"status": 1, "message": "Access denied"}

    # Wir mocken direkt die Funktion, die die Session bereitstellt
    with patch("custom_components.solarprognose_de_community.coordinator.async_get_clientsession") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_response = AsyncMock()
        mock_response.json.return_value = error_data
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        
        mock_session.get.return_value = mock_response

        # Führe Update aus - sollte nun nicht mehr hängen oder DNS brauchen
        await coordinator._async_update_data()
        
        assert coordinator.api_status == 1
        assert coordinator.api_message == "Access denied"