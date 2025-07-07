from typing import Literal

from requests import post, Response

from jablotronpy.const import HEADERS, API_URL
from jablotronpy.exceptions import BadRequestException, UnauthorizedException, SessionExpiredException, \
    JablotronApiException, InvalidSessionIdException, NoPinCodeException, IncorrectPinCodeException, \
    ControlActionException
from jablotronpy.types import JablotronService, JablotronServiceInformation, JablotronSections, JablotronThermoDevice, \
    JablotronKeyboard, JablotronProgrammableGates, JablotronServiceHistoryEvent, JablotronSectionControlResponse, \
    JablotronProgrammableGateControlResponse


class Jablotron:
    """Client for Jablotron Cloud API."""

    def __init__(self, username: str, password: str, pin_code: str | None = None) -> None:
        """
        Initialize Jablotron Cloud API client.

        :param username: email address associated with Jablotron Cloud account
        :param password: password for Jablotron Cloud account
        :param pin_code: pin code to control alarm entities
        """

        self._username = username
        self._password = password
        self._pin_code = pin_code
        self._headers = HEADERS.copy()

    def _get_provided_pin_or_default_pin(self, pin_code: str | None) -> str:
        """
        Return provided pin code or default pin code.

        :param pin_code: provided pine code to control alarm entity
        """

        if pin_code:
            return pin_code
        elif self._pin_code:
            return self._pin_code
        else:
            raise NoPinCodeException("Please, provide pin code or set default pin code.")

    def _send_request(self, endpoint: str, payload: dict) -> Response:
        """
        Send request to Jablotron Cloud API endpoint and return its response.

        :param endpoint: jablotron Cloud API endpoint
        :param payload: request payload
        """

        response = post(
            url=f"{API_URL}/{endpoint}",
            headers=self._headers,
            json=payload
        )

        match response.status_code:
            case 200:
                return response
            case 400:
                raise BadRequestException("Request is not valid, please review provided parameters.")
            case 401:
                raise UnauthorizedException("Failed to authenticate using entered credentials or session id expired.")
            case 408:
                raise SessionExpiredException("Session expired, please re-login.")
            case _:
                raise JablotronApiException(response.text)

    @staticmethod
    def _was_control_action_successful(
        response_data: JablotronSectionControlResponse | JablotronProgrammableGateControlResponse,
        component_id: str,
        state: str
    ) -> bool:
        """
        Return whether a control action was successful or not.

        :param response_data: response data
        :param component_id: component id
        :param state: desired state of the component
        """

        # Raise exception if wrong code was entered
        for error in response_data.get("control-errors", []):
            if error["control-error"] == "WRONG-CODE":
                raise IncorrectPinCodeException("Provided pin code is not valid.")
            else:
                raise ControlActionException("Control action failed with unexpected error.", error)

        # Check whether control action was successful
        components = response_data.get("states", [])
        return next(
            filter(lambda data: data["component-id"] == component_id and data["state"] == state.upper(), components),
            None
        ) is not None

    def perform_login(self) -> None:
        """
        Retrieve API session id and set it as cookie header.
        """

        response = self._send_request(
            endpoint="userAuthorize.json",
            payload=dict(login=self._username, password=self._password)
        )

        session_id = response.cookies.get("PHPSESSID")
        if session_id is None:
            raise InvalidSessionIdException("Login response does not contain a valid session id.")

        self._headers["Cookie"] = f"PHPSESSID={session_id}"

    def get_services(self) -> list[JablotronService]:
        """Return list of services associated with Jablotron Cloud account."""

        response = self._send_request(
            endpoint="serviceListGet.json",
            payload={"list-type": "EXTENDED", "visibility": "DEFAULT"}
        )

        return response.json().get("data", {}).get("services", [])

    def get_service_information(self, service_id: int) -> JablotronServiceInformation:
        """
        Return information about specific service.

        :param service_id: id of service to get information for
        """

        response = self._send_request(
            endpoint="serviceInformationGet.json",
            payload={"service-id": service_id}
        )

        return response.json().get("data", {})

    def get_sections(self, service_id: int, service_type: str = "JA100") -> JablotronSections:
        """
        Return list of sections for specified service.

        :param service_id: id of service to get sections for
        :param service_type: type of service to get sections for
        """

        response = self._send_request(
            endpoint=f"{service_type}/sectionsGet.json",
            payload={
                "connect-device": True,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": True
            }
        )

        return response.json().get("data", {})

    def get_thermo_devices(self, service_id: int, service_type: str = "JA100") -> list[JablotronThermoDevice]:
        """
        Return list of thermo devices for specified service.

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
                "service-states": False
            }
        )

        return response.json().get("data", {}).get("states", [])

    def get_keyboard_segments(self, service_id: int, service_type: str = "JA100") -> list[JablotronKeyboard]:
        """
        Return list of keyboard segments for specified service.

        :param service_id: id of service to get keyboard segments for
        :param service_type: type of service to get keyboard segments for
        """

        response = self._send_request(
            endpoint=f"{service_type}/keyboardSegmentsGet.json",
            payload={
                # Probably not necessary to connect to device, unless keyboards are often changed/renamed
                "connect-device": False,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": False
            }
        )

        return response.json().get("data", {}).get("keyboards", [])

    def get_programmable_gates(self, service_id: int, service_type: str = "JA100") -> JablotronProgrammableGates:
        """
        Return programmable gates and their states for specified service.

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
                "service-states": True
            }
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
        service_type: str = "JA100"
    ) -> list[JablotronServiceHistoryEvent]:
        """
        Return history for specified service.
        Returns last 20 events by default, but it can be configured using other params.

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
            k: v for k, v in {
                "limit": limit,
                "service-id": service_id,
                "date-from": date_from,
                "date-to": date_to,
                "event-id-from": event_id_from,
                "event-id-to": event_id_to,
            }.items() if v is not None
        }

        response = self._send_request(
            endpoint=f"{service_type}/eventHistoryGet.json",
            payload=payload_json
        )

        return response.json().get("data", {}).get("events", [])

    def control_section(
        self,
        service_id: int,
        component_id: str,
        state: Literal["ARM", "PARTIAL_ARM", "DISARM"],
        pin_code: str | None = None,
        service_type: str = "JA100",
        force: bool = False,
    ) -> bool:
        """
        Set section of specified service to desired state.

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
                "control-components": [{
                    "actions": dict(action="CONTROL-SECTION", value=state.upper()),
                    "component-id": component_id,
                    "force": force
                }]
            }
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
        """
        Set programmable gate of specified service to desired state.

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
                "control-components": [{
                    "actions": dict(action="CONTROL-PG", value=state.upper()),
                    "component-id": component_id,
                    "force": force
                }]
            }
        )

        # Validate that control action was successful
        response_data: JablotronProgrammableGateControlResponse = response.json().get("data", {})
        return self._was_control_action_successful(response_data, component_id, state)
