"""Client for Jablotron API integration."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import time
from typing import Literal

from requests import Response, post
from requests.exceptions import ReadTimeout

from jablotronpy.const import API_URL, DEFAULT_REQUEST_TIMEOUT, GRAPHQL_MAX_PAGE_SIZE, GRAPHQL_URL, HEADERS
from jablotronpy.exceptions import (
    BadGatewayException,
    BadRequestException,
    ControlActionException,
    IncorrectPinCodeException,
    InvalidSessionIdException,
    JablotronApiException,
    NoPinCodeException,
    SessionExpiredException,
    TooManyRequestsException,
    UnauthorizedException,
)
from jablotronpy.types import (
    JablotronAccessTokenResponse,
    JablotronDeviceSchedule,
    JablotronEvent,
    JablotronEventsPage,
    JablotronKeyboard,
    JablotronProgrammableGateControlResponse,
    JablotronProgrammableGates,
    JablotronSectionControlResponse,
    JablotronSections,
    JablotronService,
    JablotronServiceHistoryEvent,
    JablotronServiceInformation,
    JablotronServiceSettings,
    JablotronServiceSettingsThermostatSettings,
    JablotronServiceSettingsUpdateResponse,
    JablotronThermoDevice,
    JablotronThermoDeviceState,
)


def _parse_retry_after(value: str | None) -> int | None:
    """Parse a Retry-After header value (seconds or HTTP-date) into seconds.

    :param value: raw Retry-After header value
    """

    if value is None:
        return None

    if value.isdigit():
        return int(value)

    try:
        retry_date = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None

    return max(0, int((retry_date - datetime.now(timezone.utc)).total_seconds()))


# Renew the GraphQL access token this long before it expires.
ACCESS_TOKEN_EXPIRY_MARGIN = timedelta(seconds=60)


def _parse_token_expiration(value: str | None) -> datetime | None:
    """Parse the access token expiration timestamp, or return None if it cannot be parsed.

    A token whose expiration is unknown is not cached, so a fresh token is requested for every call.

    :param value: value of the access-token-expiration field
    """

    if not value:
        return None

    try:
        expires_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if expires_at.tzinfo is None:
        return None

    return expires_at


# GraphQL query used by get_events(), matching what the official mobile app sends to
# GRAPHQL_URL. Child events are not queried for further child events since control actions
# typically don't nest them.
_GET_EVENTS_QUERY = (
    "query GetEvents($cloudEntityId: CloudEntityID!, $pagination: Pagination, $lang: String!, "
    "$filter: EventsFilter, $eventIdsEmpty: Boolean!, $eventIds: [ID!]!, $timeZoneAvailable: Boolean!) { "
    "forEndUser { "
    "endUserDeviceManagement @skip(if: $timeZoneAvailable) { "
    "serviceSettings(params: { cloudEntityId: $cloudEntityId }) { timeZone } "
    "} "
    "events { "
    "events(sources: [$cloudEntityId], pagination: $pagination, filter: $filter) { "
    "edges { node { __typename ...EventsFragment } } "
    "pageInfo { hasNextPage endCursor startCursor } "
    "} "
    "batchEvents(sources: [$cloudEntityId], eventIds: $eventIds) @skip(if: $eventIdsEmpty) { "
    "__typename ...EventsFragment "
    "} "
    "} "
    "} "
    "} "
    "fragment EventsInvokerFragment on EventsInvoker { "
    "cloudEntityId defaultName { translation(lang: $lang) } name "
    "} "
    "fragment EventsSubjectFragment on EventsSubject { "
    "name cloudEntityId defaultName { translation(lang: $lang) } "
    "} "
    "fragment EventsEventFragment on EventsEvent { "
    "id name { translation(lang: $lang) } type occurredAt sources { cloudEntityId } "
    "invokers { __typename ...EventsInvokerFragment } subjects { __typename ...EventsSubjectFragment } icon "
    "} "
    "fragment EventsFragment on EventsEvent { "
    "__typename ...EventsEventFragment "
    "attachments { __typename ...EventsAttachementFragment } "
    "childEvents { "
    "...EventsEventFragment "
    "attachments { __typename ...EventsAttachementFragment } "
    "} "
    "} "
    "fragment EventsAttachementFragment on EventsAttachment { "
    "files { name mimeType downloadUrl } "
    "images { name mimeType downloadUrl available widthPx heightPx } "
    "videos { name mimeType downloadUrl duration } "
    "id type occurredAt "
    "}"
)


class Jablotron:
    """Client for Jablotron Cloud API."""

    def __init__(
        self,
        username: str,
        password: str,
        pin_code: str | None = None,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        """Initialize Jablotron Cloud API client.

        :param username: email address associated with Jablotron Cloud account
        :param password: password for Jablotron Cloud account
        :param pin_code: pin code to control alarm entities
        :param request_timeout: seconds to wait for the Jablotron Cloud API before raising ``requests.Timeout``
        """

        self._username = username
        self._password = password
        self._pin_code = pin_code
        self._request_timeout = request_timeout
        self._headers = HEADERS.copy()
        self._access_token: str | None = None
        self._access_token_expires_at: datetime | None = None

    def _get_provided_pin_or_default_pin(self, pin_code: str | None) -> str:
        """Return provided pin code or default pin code.

        :param pin_code: provided pine code to control alarm entity
        """

        if pin_code:
            return pin_code

        if self._pin_code:
            return self._pin_code

        raise NoPinCodeException("Please, provide pin code or set default pin code.")

    @staticmethod
    def _check_response(response: Response) -> Response:
        """Return response if it was successful, otherwise raise the matching exception.

        :param response: response returned by Jablotron Cloud API
        """

        match response.status_code:
            case 200:
                return response
            case 400:
                raise BadRequestException("Request is not valid, please review provided parameters.")
            case 401:
                raise UnauthorizedException("Failed to authenticate using entered credentials or session id expired.")
            case 408:
                raise SessionExpiredException("Session expired, please re-login.")
            case 502 | 504:
                raise BadGatewayException(response.text)
            case 429:
                raise TooManyRequestsException(
                    "Too many requests, API rate limit exceeded.",
                    retry_after=_parse_retry_after(response.headers.get("Retry-After")),
                )
            case _:
                raise JablotronApiException(response.text)

    def _send_request(self, endpoint: str, payload: dict) -> Response:
        """Send request to Jablotron Cloud API endpoint with payload in JSON format and return its response.

        :param endpoint: jablotron Cloud API endpoint
        :param payload: request payload
        """

        response = post(url=f"{API_URL}/{endpoint}", headers=self._headers, json=payload, timeout=self._request_timeout)

        return self._check_response(response)

    def _send_request_as_form_data(self, endpoint: str, payload: dict) -> Response:
        """Send request to Jablotron Cloud API endpoint with payload in form data format and return its response.

        :param endpoint: jablotron Cloud API endpoint
        :param payload: request payload
        """

        response = post(
            url=f"{API_URL}/{endpoint}",
            headers={**self._headers, "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
            data=payload,
            timeout=self._request_timeout,
        )

        return self._check_response(response)

    @staticmethod
    def _was_control_action_successful(
        response_data: JablotronSectionControlResponse | JablotronProgrammableGateControlResponse,
        component_id: str,
        state: str,
    ) -> bool:
        """Return whether a control action was successful or not.

        :param response_data: response data
        :param component_id: component id
        :param state: desired state of the component
        """

        # Raise exception if wrong code was entered
        for error in response_data.get("control-errors", []):
            if error["control-error"] == "WRONG-CODE":
                raise IncorrectPinCodeException("Provided pin code is not valid.")

            raise ControlActionException("Control action failed with unexpected error.", error)

        # Check whether control action was successful
        components = response_data.get("states", [])
        return (
            next(
                filter(
                    lambda data: data["component-id"] == component_id and data["state"] == state.upper(),
                    components,
                ),
                None,
            )
            is not None
        )

    def perform_login(self) -> None:
        """Retrieve API session id and set it as cookie header."""

        # Drop any previous session cookie so the login response always carries a fresh PHPSESSID
        self._headers.pop("Cookie", None)
        self._access_token = None
        self._access_token_expires_at = None

        response = self._send_request(
            endpoint="userAuthorize.json",
            payload={"login": self._username, "password": self._password},
        )

        session_id = response.cookies.get("PHPSESSID")
        if session_id is None:
            raise InvalidSessionIdException("Login response does not contain a valid session id.")

        self._headers["Cookie"] = f"PHPSESSID={session_id}"

    def get_services(self) -> list[JablotronService]:
        """Return list of services associated with Jablotron Cloud account."""

        response = self._send_request(
            endpoint="serviceListGet.json",
            payload={"list-type": "EXTENDED", "visibility": "DEFAULT"},
        )

        return response.json().get("data", {}).get("services", [])

    def get_service_information(self, service_id: int) -> JablotronServiceInformation:
        """Return information about specific service.

        :param service_id: id of service to get information for
        """

        response = self._send_request(endpoint="serviceInformationGet.json", payload={"service-id": service_id})

        return response.json().get("data", {})

    def get_sections(self, service_id: int, service_type: str = "JA100") -> JablotronSections:
        """Return list of sections for specified service.

        :param service_id: id of service to get sections for
        :param service_type: type of service to get sections for
        """

        response = self._send_request(
            endpoint=f"{service_type}/sectionsGet.json",
            payload={
                "connect-device": True,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": True,
            },
        )

        return response.json().get("data", {})

    def get_thermo_devices(self, service_id: int, service_type: str = "JA100") -> list[JablotronThermoDevice]:
        """Return list of thermo devices for specified service.

        :param service_id: id of service to get thermo devices for
        :param service_type: type of service to get thermo devices for
        """

        response = self._send_request(
            endpoint=f"{service_type}/thermoDevicesGet.json",
            payload={
                # Rather connect to device to get actual values
                "connect-device": True,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": False,
            },
        )

        data = response.json().get("data", {})
        states = data.get("states", [])
        devices = data.get("thermo-devices", [])

        device_by_id = {d["object-device-id"]: d for d in devices}

        result: list[JablotronThermoDevice] = []

        for state in states:
            dev_id = state["object-device-id"]
            meta = device_by_id.get(dev_id, {})
            result.append(
                {
                    "object-device-id": dev_id,
                    "name": meta.get("name", ""),
                    "temperature": state.get("temperature"),
                    "last-temperature-time": state.get("last-temperature-time"),
                    "thermo-device": device_by_id.get(dev_id, {}),
                    "state": state,
                }
            )

        return result

    def get_keyboard_segments(self, service_id: int, service_type: str = "JA100") -> list[JablotronKeyboard]:
        """Return list of keyboard segments for specified service.

        :param service_id: id of service to get keyboard segments for
        :param service_type: type of service to get keyboard segments for
        """

        response = self._send_request(
            endpoint=f"{service_type}/keyboardSegmentsGet.json",
            payload={
                # Probably not necessary to connect to device, unless keyboards are often
                # changed/renamed
                "connect-device": False,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": False,
            },
        )

        return response.json().get("data", {}).get("keyboards", [])

    def get_programmable_gates(self, service_id: int, service_type: str = "JA100") -> JablotronProgrammableGates:
        """Return programmable gates and their states for specified service.

        :param service_id: id of service to get programmable gates for
        :param service_type: type of service to get programmable gates for
        """

        response = self._send_request(
            endpoint=f"{service_type}/programmableGatesGet.json",
            payload={
                # Rather connect to device to get actual values
                "connect-device": True,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": True,
            },
        )

        return response.json().get("data", {})

    def get_service_history(
        self,
        service_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
        event_id_from: str | None = None,
        event_id_to: str | None = None,
        limit: int = 20,
        service_type: str = "JA100",
    ) -> list[JablotronServiceHistoryEvent]:
        """Return history for specified service.

        Returns last 20 events by default, but it can be configured using other params.

        Note: this REST endpoint has stopped working for most accounts and now returns
        a ``400 METHOD.NOT-SUPPORTED`` error regardless of the parameters passed (see
        issue #24). Prefer :meth:`get_events`, which fetches the same kind of history
        (including section arm/disarm events) through the GraphQL API that the official
        mobile app uses instead.

        :param service_id: id of service to get history for
        :param date_from: date from which historical events should be fetched
        :param date_to: date to which historical events should be fetched
        :param event_id_from: event id from which historical events should be fetched
        :param event_id_to: event id to which historical events should be fetched
        :param limit: number of historical events to fetch
        :param service_type: type of service to get history for
        """

        # Construct payload based on user input
        payload_json: dict[str, str | int] = {
            k: v
            for k, v in {
                "limit": limit,
                "service-id": service_id,
                "date-from": date_from,
                "date-to": date_to,
                "event-id-from": event_id_from,
                "event-id-to": event_id_to,
            }.items()
            if v is not None
        }

        response = self._send_request(endpoint=f"{service_type}/eventHistoryGet.json", payload=payload_json)

        return response.json().get("data", {}).get("events", [])

    def get_access_token(self, force_renew: bool = False) -> str:
        """Return a short-lived bearer token for the Jablotron GraphQL API.

        This token is required to call :meth:`get_events` and is obtained through the
        same authenticated session (cookie) as the rest of the REST API, so
        :meth:`perform_login` must have been called first.

        :param force_renew: request a new token even if the current session already has one
        """

        response = self._send_request(
            endpoint="accessTokenGet.json",
            payload={"force-renew": force_renew},
        )
        response_data: JablotronAccessTokenResponse = response.json().get("data", {})
        token = response_data.get("access-token")
        if not token:
            raise JablotronApiException("accessTokenGet.json response did not contain an access-token.")

        self._access_token = token
        self._access_token_expires_at = _parse_token_expiration(response_data.get("access-token-expiration"))
        return token

    def _get_valid_access_token(self) -> str:
        """Return the cached GraphQL access token, or request a new one if it is missing or (about to be) expired."""

        if (
            self._access_token is not None
            and self._access_token_expires_at is not None
            and datetime.now(timezone.utc) < self._access_token_expires_at - ACCESS_TOKEN_EXPIRY_MARGIN
        ):
            return self._access_token

        return self.get_access_token()

    def _send_graphql_request(self, query: str, variables: dict) -> dict:
        """Send query to the Jablotron GraphQL API and return its ``data``.

        The cached access token is renewed once if the API rejects it as unauthorized.

        :param query: GraphQL query
        :param variables: variables for the query
        """

        for attempt in range(2):
            access_token = self._get_valid_access_token() if attempt == 0 else self.get_access_token(force_renew=True)
            response = post(
                url=GRAPHQL_URL,
                headers={
                    "x-vendor-id": self._headers["x-vendor-id"],
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "variables": variables},
                timeout=self._request_timeout,
            )
            if response.status_code != 401:
                break

        self._check_response(response)

        try:
            body = response.json()
        except ValueError as error:
            raise JablotronApiException(f"GraphQL response is not valid JSON: {response.text}") from error

        if body.get("errors"):
            raise JablotronApiException(f"GraphQL request failed: {body['errors']}")

        data = body.get("data")
        if data is None:
            raise JablotronApiException(f"GraphQL response did not contain data: {body}")

        return data

    def get_events_page(
        self,
        service_id: int,
        service_type: str,
        after: str | None = None,
        language: str = "en",
        page_size: int = GRAPHQL_MAX_PAGE_SIZE,
    ) -> JablotronEventsPage:
        """Return a single page of event history for a service via the GraphQL API, newest first.

        Use this instead of :meth:`get_events` to walk the complete history: pass the
        returned ``end-cursor`` as ``after`` until ``has-next-page`` is false.

        :param service_id: id of service to get events for
        :param service_type: panel type of the service as returned by :meth:`get_services`
            (``service-type``, e.g. ``JA100F``), used to build the GraphQL cloud entity id
        :param after: cursor of the previous page, or None to start at the newest event
        :param language: language code used for the translated event name
        :param page_size: events requested per page (1-20; the API rejects larger pages)
        """

        if not 1 <= page_size <= GRAPHQL_MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {GRAPHQL_MAX_PAGE_SIZE}, got {page_size}.")

        data = self._send_graphql_request(
            query=_GET_EVENTS_QUERY,
            variables={
                "cloudEntityId": f"SERVICE_{service_type}:{service_id}",
                "pagination": {"first": page_size, "after": after},
                "lang": language,
                "filter": {},
                "eventIdsEmpty": True,
                "eventIds": [],
                "timeZoneAvailable": True,
            },
        )

        page = data["forEndUser"]["events"]["events"]
        page_info = page["pageInfo"]
        return {
            "events": [edge["node"] for edge in page["edges"]],
            "has-next-page": page_info["hasNextPage"],
            "end-cursor": page_info["endCursor"],
        }

    def get_events(
        self,
        service_id: int,
        service_type: str,
        language: str = "en",
        page_size: int = GRAPHQL_MAX_PAGE_SIZE,
        max_pages: int | None = 10,
    ) -> list[JablotronEvent]:
        """Return event history for a service via the GraphQL API, newest first.

        The REST ``eventHistoryGet.json`` endpoint used by :meth:`get_service_history` no
        longer works. The official mobile app instead fetches event history (including
        section arm/disarm events, with the invoking user and the affected section)
        through a separate GraphQL API. This method replicates that request.

        Pages are fetched until there are no more events or ``max_pages`` is reached, so
        with the default ``max_pages`` only the most recent events are returned. Pass
        ``max_pages=None`` to fetch the complete history, or use :meth:`get_events_page`
        to paginate yourself.

        :param service_id: id of service to get events for
        :param service_type: panel type of the service as returned by :meth:`get_services`
            (``service-type``, e.g. ``JA100F``), used to build the GraphQL cloud entity id
        :param language: language code used for the translated event name
        :param page_size: events requested per page (1-20; the API rejects larger pages)
        :param max_pages: maximum number of pages to fetch, or None for no limit
        """

        events: list[JablotronEvent] = []
        after: str | None = None
        pages_fetched = 0

        while max_pages is None or pages_fetched < max_pages:
            page = self.get_events_page(service_id, service_type, after, language, page_size)
            events.extend(page["events"])
            pages_fetched += 1

            if not page["has-next-page"]:
                break
            after = page["end-cursor"]

        return events

    def control_section(
        self,
        service_id: int,
        component_id: str,
        state: Literal["ARM", "PARTIAL_ARM", "DISARM"],
        pin_code: str | None = None,
        service_type: str = "JA100",
        force: bool = False,
    ) -> bool:
        """Set section of specified service to desired state.

        :param service_id: id of service to control section for
        :param component_id: if of component to control
        :param state: desired state to set section to
        :param pin_code: pin code used to authorize action
        :param service_type: type of service to control section for
        :param force: override blockage of section
        """

        pin_code = self._get_provided_pin_or_default_pin(pin_code)
        response = self._send_request(
            endpoint=f"{service_type}/controlComponent.json",
            payload={
                "service-id": service_id,
                "authorization": {"authorization-code": pin_code},
                "control-components": [
                    {
                        "actions": {"action": "CONTROL-SECTION", "value": state.upper()},
                        "component-id": component_id,
                        "force": force,
                    }
                ],
            },
        )

        # Validate that control action was successful
        response_data: JablotronSectionControlResponse = response.json().get("data", {})
        return self._was_control_action_successful(response_data, component_id, state)

    def control_programmable_gate(
        self,
        service_id: int,
        component_id: str,
        state: Literal["ON", "OFF"],
        pin_code: str | None = None,
        service_type: str = "JA100",
        force: bool = False,
    ) -> bool:
        """Set programmable gate of specified service to desired state.

        :param service_id: id of service to control programmable gate for
        :param component_id: if of component to control
        :param state: desired state to set programmable gate to
        :param pin_code: pin code used to authorize action
        :param service_type: type of service to control programmable gate for
        :param force: override blockage of programmable gate
        """

        pin_code = self._get_provided_pin_or_default_pin(pin_code)
        response = self._send_request(
            endpoint=f"{service_type}/controlComponent.json",
            payload={
                "service-id": service_id,
                "authorization": {"authorization-code": pin_code},
                "control-components": [
                    {
                        "actions": {"action": "CONTROL-PG", "value": state.upper()},
                        "component-id": component_id,
                        "force": force,
                    }
                ],
            },
        )

        # Validate that control action was successful
        response_data: JablotronProgrammableGateControlResponse = response.json().get("data", {})
        return self._was_control_action_successful(response_data, component_id, state)

    def get_service_settings(self, service_id: int, service_type: str = "JA100") -> JablotronServiceSettings:
        """Return information about settings for a service.

        :param service_id: id of service to get settings for
        :param service_type: type of service to get settings for
        """

        response = self._send_request(
            endpoint="getServiceSettings.json",
            payload={"serviceId": service_id, "service": service_type.lower()},
        )

        response_data: JablotronServiceSettings = response.json()
        return response_data

    def update_service_settings(
        self,
        service_id: int,
        thermostat_settings: JablotronServiceSettingsThermostatSettings,
        service_type: str = "JA100",
    ) -> JablotronServiceSettingsUpdateResponse:
        """Update service settings.

        :param service_id: id of service to control thermo device for
        :param thermostat_settings: thermostat settings to update, must be complete JablotronServiceSettingsThermostatSettings
        :param service_type: type of service to control thermo device for
        """

        response = self._send_request_as_form_data(
            endpoint="updateServiceSettings.json",
            payload={
                "service_data": json.dumps(
                    [
                        {
                            "serviceId": service_id,
                            "service": service_type.lower(),
                            "data": {"thermostats": [thermostat_settings]},
                        }
                    ]
                )
            },
        )

        response_body: JablotronServiceSettingsUpdateResponse = response.json()

        if not response_body["status"]:
            raise ControlActionException(
                "Service settings update failed with unexpected error(s):",
                response_body["error_status"],
                response_body["error_message"],
            )

        return response_body

    @staticmethod
    def _thermo_device_state_matches(
        state: JablotronThermoDeviceState,
        heating_mode: str | None,
        temperature: float | None,
    ) -> bool:
        """Return whether thermo device state reflects the requested heating mode and temperature.

        :param state: current state of the thermo device
        :param heating_mode: requested heating mode or None if it was not changed
        :param temperature: requested temperature or None if it was not changed
        """

        mode = state.get("mode")
        if heating_mode == "OFF" and mode != "STAND_BY":
            return False
        # Turning heating ON restores the previous mode, which can be any mode except STAND_BY
        if heating_mode == "ON" and mode in (None, "STAND_BY"):
            return False
        if heating_mode in ("MANUAL", "SCHEDULED") and mode != heating_mode:
            return False

        temperature_set = state.get("temperature-set")
        return temperature is None or (temperature_set is not None and abs(temperature_set - temperature) < 0.01)

    def _wait_for_thermo_device_state(
        self,
        service_id: int,
        object_device_id: str,
        heating_mode: str | None,
        temperature: float | None,
        service_type: str,
        timeout: float,
        interval: float,
    ) -> JablotronThermoDeviceState | None:
        """Poll thermo device until it reflects the requested change and return its state, or None on timeout.

        :param service_id: id of service the thermo device belongs to
        :param object_device_id: id of thermo device to poll
        :param heating_mode: requested heating mode or None if it was not changed
        :param temperature: requested temperature or None if it was not changed
        :param service_type: type of service the thermo device belongs to
        :param timeout: maximum number of seconds to wait
        :param interval: number of seconds between polls
        """

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            time.sleep(min(interval, remaining))

            try:
                devices = self.get_thermo_devices(service_id, service_type)
            except (BadGatewayException, ReadTimeout):
                continue

            device = next((d for d in devices if d["object-device-id"] == object_device_id), None)
            if device is not None and self._thermo_device_state_matches(device["state"], heating_mode, temperature):
                return device["state"]

    def control_thermo_device_with_response(
        self,
        service_id: int,
        object_device_id: str,
        heating_mode: Literal["MANUAL", "SCHEDULED", "OFF", "ON"] | None = None,
        temperature: float | None = None,
        service_type: str = "JA100",
        confirm_timeout: float = 60,
        confirm_interval: float = 3,
    ) -> JablotronThermoDeviceState | None:
        """Set thermo device of specified service to desired heating mode and return the device's state.

        Jablotron Cloud often answers this request with 502 Bad Gateway after a few seconds while
        the change is still applied 20-50 seconds later. In that case, or when no answer arrives
        within the request timeout, the thermo device is polled for up to ``confirm_timeout``
        seconds and its state is returned once it reflects the requested change. If it does not,
        the original :class:`BadGatewayException` or ``requests.ReadTimeout`` is raised.

        :param service_id: id of service to control thermo device for
        :param object_device_id: id of thermo device to control
        :param heating_mode: heating mode to set or None to keep the current value
        :param temperature: temperature to set or None to keep the current value
        :param service_type: type of service to control thermo device for
        :param confirm_timeout: seconds to wait for the change after a 502/504 or read timeout, 0 to raise immediately
        :param confirm_interval: seconds between polls while waiting for the change
        """

        if heating_mode == "SCHEDULED" and temperature is not None:
            # When temperature is set and heating mode is set to SCHEDULED,
            # heating mode is set to MANUAL_TEMP instead.
            # => Raise exception in this case to prevent unexpected behaviour.
            raise ControlActionException(f"Temperature cannot be set when setting heating mode to {heating_mode}.")

        actions = {}
        if heating_mode is not None:
            actions["set-heating-mode"] = heating_mode
        if temperature is not None:
            actions["set-temperature"] = temperature

        try:
            response = self._send_request(
                endpoint=f"{service_type}/controlThermoDevice.json",
                payload={
                    "service-id": service_id,
                    "control-components": [
                        {
                            "actions": actions,
                            "component-id": object_device_id,
                        }
                    ],
                },
            )
        except (BadGatewayException, ReadTimeout):
            # The request reached Jablotron Cloud but no answer came back in time, so the change may still be applied
            if confirm_timeout <= 0:
                raise

            state = self._wait_for_thermo_device_state(
                service_id,
                object_device_id,
                heating_mode,
                temperature,
                service_type,
                confirm_timeout,
                confirm_interval,
            )
            if state is None:
                raise

            return state

        response_body = response.json()
        response_data = response_body.get("data", {})
        response_errors = response_data.get("control-errors", [])

        if len(response_errors) > 0:
            raise ControlActionException(
                "Thermo device control failed with unexpected error(s):",
                *response_errors,
            )

        states = response_data.get("states", [])
        return next(
            filter(lambda state: state["object-device-id"] == object_device_id, states),
            None,
        )

    def control_thermo_device(
        self,
        service_id: int,
        object_device_id: str,
        heating_mode: Literal["MANUAL", "SCHEDULED", "OFF", "ON"] | None = None,
        temperature: float | None = None,
        service_type: str = "JA100",
        confirm_timeout: float = 60,
        confirm_interval: float = 3,
    ) -> bool:
        """Set thermo device of specified service to desired heating mode and return boolean when the change is successful.

        See :meth:`control_thermo_device_with_response` for how 502 Bad Gateway responses and read timeouts are handled.

        :param service_id: id of service to control thermo device for
        :param object_device_id: id of thermo device to control
        :param heating_mode: heating mode to set or None to keep the current value
        :param temperature: temperature to set or None to keep the current value
        :param service_type: type of service to control thermo device for
        :param confirm_timeout: seconds to wait for the change after a 502/504 or read timeout, 0 to raise immediately
        :param confirm_interval: seconds between polls while waiting for the change
        """

        state = self.control_thermo_device_with_response(
            service_id, object_device_id, heating_mode, temperature, service_type, confirm_timeout, confirm_interval
        )
        return state is not None

    def get_device_schedule(
        self,
        service_id: str,
        device_type: str,
        device_id: str,
        room_id: str,
        service_type: str = "JA100",
    ) -> JablotronDeviceSchedule:
        """Return information about a schedule.

        :param service_id: id of service to get schedule for
        :param device_type: device_type to get schedule for
        :param device_id: device_id to get schedule for
        :param room_id: room_id to get schedule for
        :param service_type: type of service to get schedule for
        """

        response = self._send_request(
            endpoint="getDeviceSchedule.json",
            payload={
                "status": True,
                "type": device_type,
                "id": device_id,
                "parent_type": service_type.lower(),
                "room_id": room_id,
                "parent_id": service_id,
            },
        )

        response_data: JablotronDeviceSchedule = response.json()
        return response_data
