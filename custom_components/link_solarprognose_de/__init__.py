"""Solarprognose.de (Community) Integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .sensor import SolarPrognoseCoordinator

_LOGGER = logging.getLogger(__name__)

# Die Domäne muss mit deinem manifest.json übereinstimmen
DOMAIN = "solarprognose_de_community"

# Liste der Plattformen, die eingerichtet werden sollen
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über die Benutzeroberfläche auf."""
    
    # 1. Daten-Struktur in hass initialisieren, falls nicht vorhanden
    hass.data.setdefault(DOMAIN, {})

    # 2. Konfiguration abrufen (bevorzugt aus Optionen, sonst aus Basis-Daten)
    # Dies ermöglicht Änderungen über das "Konfigurieren"-Menü ohne Neuinstallation.
    api_url = entry.options.get("api_url", entry.data.get("api_url"))
    api_key = entry.options.get("api_key", entry.data.get("api_key"))

    # 3. Coordinator erstellen
    coordinator = SolarPrognoseCoordinator(
        hass=hass, 
        api_url=api_url, 
        api_key=api_key
    )

    # 4. Ersten Abruf der Daten versuchen
    # Wenn die API nicht erreichbar ist (z.B. kein Internet beim Start), 
    # markiert ConfigEntryNotReady die Integration für einen späteren Versuch.
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Solarprognose API nicht erreichbar: {ex}") from ex

    # 5. Coordinator global für die Sensoren speichern.
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # 6. Plattformen (Sensoren) laden
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 7. Listener für Options-Updates registrieren
    # Wenn der User auf "Konfigurieren" klickt, wird die Integration neu geladen.
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, wenn die Optionen (Key/URL) im UI geändert wurden."""
    # Bewirkt ein Entladen und erneutes Laden der Integration (async_setup_entry).
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlädt die Integration und entfernt alle Entitäten."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Speicher im globalen Objekt freigeben.
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok