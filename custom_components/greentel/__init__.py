import logging

from .greentel import greentelClient
from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    # Initialize the Client
    client  = greentelClient(conf.get('phonenumber'), conf.get('password'))
    hass.data[DOMAIN] = {
        "client": client
    }

    # Add sensors
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform('sensor', DOMAIN, conf, config)
    )

    # Initialization was successful.
    return True