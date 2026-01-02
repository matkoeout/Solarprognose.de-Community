from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .sensor import SolarPrognoseCoordinator 

DOMAIN = "link_solarprognose_de"
PLATFORMS = ["sensor"]

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Wird aufgerufen, wenn die Optionen (Key/ID) geändert werden."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über die Benutzeroberfläche auf."""
    hass.data.setdefault(DOMAIN, {})
    
    api_url = entry.options.get( "api_url", entry.data.get("api_url"))
    api_key = entry.options.get( "api_key", entry.data.get("api_key"))

    coordinator = SolarPrognoseCoordinator( hass=hass, api_url=api_url, api_key=api_key)

    # 3. Ersten Abruf versuchen
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Solarprognose API nicht erreichbar: {ex}")

    # 4. Daten für Sensoren speichern
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Listener für Options-Updates
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlädt die Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True