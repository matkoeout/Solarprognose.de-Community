import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Minimaler Patch, um IntegrationNotFound Fehler zu vermeiden."""
    mock_integration = MagicMock()
    mock_integration.domain = "solarprognose_de_community"
    
    # Wir simulieren nur das Vorhandensein der Integration, mehr nicht.
    with patch("homeassistant.loader.async_get_integration", return_value=mock_integration), \
         patch("homeassistant.setup.async_process_deps_reqs", return_value=True):
        
        hass.data["integrations"] = {"solarprognose_de_community": mock_integration}
        hass.config.components.add("solarprognose_de_community")
        yield

@pytest.fixture(autouse=True)
def mock_dns_resolver():
    """Verhindert DNS-Anfragen."""
    with patch("aiodns.DNSResolver.getaddrinfo", side_effect=Exception("DNS blocked")):
        yield

@pytest.fixture
def mock_api_data():
    """Simuliert eine API-Antwort fuer Tests."""
    return {
        "status": 0,
        "message": "OK",
        "preferredNextApiRequestAt": {"epochTimeUtc": 1700000000},
        "data": {
            "1700000000": [1.5],
            "1700003600": [2.0]
        }
    }