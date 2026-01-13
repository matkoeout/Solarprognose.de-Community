"""Test the Solarprognose.de Community config flow."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Wir importieren die Klasse direkt (Unit-Test-Ansatz)
from custom_components.solarprognose_de_community import config_flow
from custom_components.solarprognose_de_community.const import DOMAIN

# --------------------------------------------------------------------------
# HELPER: MOCK SESSION
# --------------------------------------------------------------------------
def get_mock_session(status=0):
    """Erstellt eine gefakte aiohttp ClientSession."""
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"status": status})
    
    mock_ctx = MagicMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_ctx
    return mock_session

# --------------------------------------------------------------------------
# TESTS
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_form_direct(hass: HomeAssistant) -> None:
    """Testet den Happy-Path (Erfolgreiches Setup)."""
    flow = config_flow.SolarPrognoseConfigFlow()
    flow.hass = hass

    # 1. Initialisierung
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # 2. Formular absenden (mit Mock für HTTP)
    mock_session = get_mock_session(status=0)
    patch_target = "custom_components.solarprognose_de_community.config_flow.async_get_clientsession"

    with patch(patch_target, return_value=mock_session):
        result2 = await flow.async_step_user(user_input={
            "name": "Meine Solaranlage",
            "api_key": "test_key_123"
        })

    # 3. Prüfung
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Meine Solaranlage"
    assert result2["data"]["api_key"] == "test_key_123"
    mock_session.get.assert_called_once()


@pytest.mark.asyncio
async def test_user_form_missing_data(hass: HomeAssistant) -> None:
    """Testet Fehler bei fehlenden Eingaben."""
    flow = config_flow.SolarPrognoseConfigFlow()
    flow.hass = hass

    await flow.async_step_user(user_input=None)

    # Leere Eingabe simulieren (aber Dictionary ist nicht leer, nur api_key fehlt)
    result = await flow.async_step_user(user_input={"name": "Nur Name"})

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "missing_api"}


@pytest.mark.asyncio
async def test_user_form_api_error(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Testet, dass der Flow auch bei API-Fehler durchläuft (Warnung im Log)."""
    flow = config_flow.SolarPrognoseConfigFlow()
    flow.hass = hass

    await flow.async_step_user(user_input=None)

    # Status -1 simulieren -> Sollte Warnung loggen
    mock_session = get_mock_session(status=-1)
    patch_target = "custom_components.solarprognose_de_community.config_flow.async_get_clientsession"

    with patch(patch_target, return_value=mock_session):
        result = await flow.async_step_user(user_input={
            "name": "Anlage mit Fehler",
            "api_key": "bad_key"
        })

    # Prüfung: Warnung wurde geloggt? "Validierung fehlgeschlagen"
    assert "Validierung fehlgeschlagen" in caplog.text
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


@pytest.mark.asyncio
async def test_user_form_network_exception(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Testet, dass der Flow auch bei Netzwerk-Exception (Timeout etc.) nicht abstürzt."""
    flow = config_flow.SolarPrognoseConfigFlow()
    flow.hass = hass

    await flow.async_step_user(user_input=None)

    # Wir simulieren einen Crash (z.B. Timeout)
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Netzwerk tot")
    
    patch_target = "custom_components.solarprognose_de_community.config_flow.async_get_clientsession"

    # KORREKTUR: Wir nutzen 'caplog' als Argument (oben definiert) und kein 'with pytest.LogCaptureFixture'
    with patch(patch_target, return_value=mock_session):
        result = await flow.async_step_user(user_input={
            "name": "Anlage Offline",
            "api_key": "offline_key"
        })

    # Prüfung: Warnung wurde geloggt? "Server nicht erreichbar"
    assert "Server nicht erreichbar" in caplog.text
    # Setup wird trotzdem erlaubt
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


@pytest.mark.asyncio
async def test_get_options_flow(hass: HomeAssistant) -> None:
    """Testet, ob der Options-Flow korrekt initialisiert wird."""
    entry = MockConfigEntry(domain=DOMAIN)
    options_flow = config_flow.SolarPrognoseConfigFlow.async_get_options_flow(entry)
    assert isinstance(options_flow, config_flow.SolarPrognoseOptionsFlowHandler)


@pytest.mark.asyncio
async def test_options_flow_direct(hass: HomeAssistant) -> None:
    """Testet den Options-Flow (Konfigurations-Dialog)."""
    entry = MockConfigEntry(
        domain=DOMAIN, 
        data={"api_key": "old_key", "api_url": "old_url"}
    )
    entry.add_to_hass(hass)

    flow = config_flow.SolarPrognoseOptionsFlowHandler()
    flow.hass = hass
    # WORKAROUND: Wir setzen _config_entry direkt
    flow._config_entry = entry

    # --- SCHRITT A: Init ---
    result = await flow.async_step_init(user_input=None)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    
    # Defaults prüfen
    schema = result["data_schema"].schema
    api_key_option = next(k for k in schema if k == "api_key")
    default_val = api_key_option.default
    if callable(default_val):
        default_val = default_val()
    assert default_val == "old_key"

    # --- SCHRITT B: Speichern ---
    mock_session = get_mock_session(status=0)
    patch_target = "custom_components.solarprognose_de_community.config_flow.async_get_clientsession"

    with patch(patch_target, return_value=mock_session):
        result2 = await flow.async_step_init(user_input={
            "api_key": "new_super_key",
            "api_url": "http://new.url"
        })

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"]["api_key"] == "new_super_key"