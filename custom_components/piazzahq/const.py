"""Constants for the Piazza HQ integration."""

DOMAIN = "piazzahq"

CONF_HOST = "host"
CONF_TOKEN = "token"

DEFAULT_PORT = 3000

# How often to re-poll the discovery endpoints for new/removed screens,
# displays and saved layouts, so a household doesn't need to reload the
# integration by hand every time they add one in Piazza HQ itself.
UPDATE_INTERVAL_SECONDS = 300

MANUFACTURER = "Piazza HQ"
