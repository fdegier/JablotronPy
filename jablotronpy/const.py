"""Constants for Jablotron API integration."""

API_VERSION = "2.2"
API_URL = f"https://api.jablonet.net/api/{API_VERSION}"
GRAPHQL_URL = "https://graph.jablotron.cloud/graphql"
# Seconds to wait for a response before giving up, so a hanging connection cannot block forever.
DEFAULT_REQUEST_TIMEOUT = 30
# The GraphQL API rejects event pages larger than roughly 20-24 with a generic validation error.
GRAPHQL_MAX_PAGE_SIZE = 20
HEADERS = {
    "x-vendor-id": "JABLOTRON:Jablotron",
    "x-client-version": "MYJ-PUB-ANDROID-15",
    "accept-encoding": "*",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "en",
}
