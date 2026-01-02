import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "link_solarprognose_de"


class SolarPrognoseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solarprognose.de."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")
            api_url = user_input.get("api_url")

            # Mindestens API-Key ODER URL erforderlich
            if not api_key and not api_url:
                errors["base"] = "missing_api"

            if not errors:
                return self.async_create_entry(
                    title=user_input.get("name", "Solarprognose"),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Solarprognose"): str,
                    vol.Optional("api_key"): str,
                    vol.Optional("api_url"): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolarPrognoseOptionsFlowHandler(config_entry)


class SolarPrognoseOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Solarprognose.de."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")
            api_url = user_input.get("api_url")

            # Auch hier: mindestens eines notwendig
            if not api_key and not api_url:
                errors["base"] = "missing_api"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        current_api_key = self.config_entry.options.get(
            "api_key", self.config_entry.data.get("api_key", "")
        )
        current_api_url = self.config_entry.options.get(
            "api_url", self.config_entry.data.get("api_url", "")
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("api_key", default=current_api_key): str,
                    vol.Optional("api_url", default=current_api_url): str,
                }
            ),
            errors=errors,
        )
