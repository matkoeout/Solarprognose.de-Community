"""Lovelace dashboard strategy for Solarprognose."""
from __future__ import annotations

from homeassistant.components.lovelace.strategies import FrontendStrategy
from homeassistant.core import HomeAssistant

class SolarPrognoseDashboardStrategy(FrontendStrategy):
    """Strategy to create a solar forecast dashboard."""

    async def async_generate(self, config, hass: HomeAssistant):
        """Generate the dashboard config."""
        
        # Wir bauen hier exakt dein gewünschtes Grid-Layout nach
        return {
            "title": "Solarprognose",
            "views": [
                {
                    "title": "Übersicht",
                    "cards": [
                        {
                            "type": "grid",
                            "columns": 1,
                            "square": False,
                            "cards": [
                                {
                                    "type": "vertical-stack",
                                    "cards": [
                                        {
                                            "type": "heading",
                                            "heading": "Solar-Vorhersage",
                                            "icon": "mdi:sun-clock"
                                        },
                                        {
                                            "type": "grid",
                                            "columns": 2,
                                            "square": False,
                                            "cards": [
                                                {
                                                    "type": "tile",
                                                    "entity": "sensor.solarprognose_heute_gesamt",
                                                    "color": "orange"
                                                },
                                                {
                                                    "type": "tile",
                                                    "entity": "sensor.solarprognose_resttag",
                                                    "color": "amber"
                                                }
                                            ]
                                        },
                                        {
                                            "type": "energy-solar-graph",
                                            "title": "Stündliche Kurve"
                                        },
                                        {
                                            "type": "entities",
                                            "entities": [
                                                {"entity": "sensor.solarprognose_morgen_gesamt"},
                                                {"entity": "sensor.solarprognose_api_status"},
                                                {"entity": "sensor.solarprognose_letzte_abfrage"}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }