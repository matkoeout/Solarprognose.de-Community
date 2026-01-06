"""Solarprognose.de (Community) Integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

# 1. Zuerst den Coordinator importieren (Kern-Logik)
from .sensor import SolarPrognoseCoordinator

# 2. Dann die Dashboard-Strategie importieren
from .dashboard import SolarPrognoseDashboardStrategy 

_LOGGER = logging.getLogger(__name__)

DOMAIN = "solarprognose_de_community"
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration auf."""
    
    hass.data.setdefault(DOMAIN, {})

    # Konfiguration laden
    api_url = entry.options.get("api_url", entry.data.get("api_url"))
    api_key = entry.options.get("api_key", entry.data.get("api_key"))

    coordinator = SolarPrognoseCoordinator(
        hass=hass, 
        api_url=api_url, 
        api_key=api_key
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Solarprognose API nicht erreichbar: {ex}") from ex

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # --- Strategie-Registrierung ---
    if "lovelace" in hass.config.components:
        try:
            # Versuch 1: Moderner Pfad (HA 2024.12+)
            from homeassistant.components.lovelace.dashboard import async_register_strategy
            async_register_strategy(hass, DOMAIN, "view", SolarPrognoseDashboardStrategy)
            _LOGGER.info("Solarprognose Strategie registriert (Pfad: dashboard)")
        except (ImportError, AttributeError):
            try:
                # Versuch 2: Alternativer Pfad
                from homeassistant.components.lovelace import async_register_strategy
                async_register_strategy(hass, DOMAIN, "view", SolarPrognoseDashboardStrategy)
                _LOGGER.info("Solarprognose Strategie registriert (Pfad: lovelace)")
            except Exception as err:
                _LOGGER.error("Registrierung fehlgeschlagen: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update bei Konfigurationsänderung."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entladen der Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok