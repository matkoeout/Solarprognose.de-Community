import voluptuous as vol
import aiohttp
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "solarprognose_de_community"

async def validate_input(hass, data):
    api_key = data.get("api_key")
    url = data.get("api_url") or (
        "https://www.solarprognose.de/web/solarprediction/api/v1"
        f"?access-token={api_key}&type=hourly&_format=json"
    )

    try:
        async with async_timeout.timeout(10):
            session = async_get_clientsession(hass)
            async with session.get(url) as response:
                if response.status != 200:
                    return "cannot_connect"
                res = await response.json()
                if res.get("status") != 0:
                    return "invalid_auth"
    except (aiohttp.ClientError, Exception):
        return "cannot_connect"
    return None

class SolarPrognoseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input:
            if not user_input.get("api_key") and not user_input.get("api_url"):
                errors["base"] = "missing_api"
            elif error_key := await validate_input(self.hass, user_input):
                errors["base"] = error_key
            else:
                return self.async_create_entry(title=user_input.get("name", "Solarprognose"), data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="Solarprognose"): str,
                vol.Optional("api_key"): str,
                vol.Optional("api_url"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarPrognoseOptionsFlowHandler()

class SolarPrognoseOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input:
            if error_key := await validate_input(self.hass, user_input):
                errors["base"] = error_key
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("api_key", default=self.config_entry.options.get("api_key", self.config_entry.data.get("api_key", ""))): str,
                vol.Optional("api_url", default=self.config_entry.options.get("api_url", self.config_entry.data.get("api_url", ""))): str,
            }),
            errors=errors,
        )