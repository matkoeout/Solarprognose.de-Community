"""Diagnostics support for Solarprognose."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN

# Felder, die direkt im Dictionary geschwaerzt werden
TO_REDACT = {"api_key", "access-token", "api_url"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Gibt Diagnoseinformationen zurueck und maskiert dabei Geheimnisse."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Konfigurationsdaten schwaerzen
    diag_data = async_redact_data(entry.as_dict(), TO_REDACT)
    
    # Zusaetzlicher Schutz: Falls der Key in der URL steckt, diesen Teil maskieren
    if "api_url" in diag_data.get("data", {}):
        url = diag_data["data"]["api_url"]
        diag_data["data"]["api_url"] = re.sub(r"access-token=[^&]+", "access-token=REDACTED", url)
    
    if "api_url" in diag_data.get("options", {}):
        url = diag_data["options"]["api_url"]
        diag_data["options"]["api_url"] = re.sub(r"access-token=[^&]+", "access-token=REDACTED", url)

    return {
        "config_entry": diag_data,
        "coordinator_data": coordinator.data,
        "api_status": coordinator.api_status,
        "api_message": coordinator.api_message,
    }