# tests/test_energy.py
from custom_components.solarprognose_de_community.energy import async_get_solar_forecast

async def test_energy_setup(hass):
    """Bringt energy.py auf 100% Coverage."""
    result = await async_get_solar_forecast(hass, "test")
    assert result is not None