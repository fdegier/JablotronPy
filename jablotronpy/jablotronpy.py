import logging
from typing import Union, Any

import requests

logger = logging.getLogger(__name__)


class UnexpectedResponse(Exception):
    """Specialization of exception for cases when request does note return expected data."""
    pass


class Jablotron:
    def __init__(self, username: str, password: str, pin_code: Union[str, int]):
        """
        :param username: Email address used for Jablotron
        :param password: Password used for Jablotron
        """
        self.headers = {
            "x-vendor-id": "JABLOTRON:Jablotron",
            "x-client-version": "MYJ-PUB-ANDROID-15",
            "accept-encoding": "*",
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Accept-Language': 'en',
        }
        api_version = "2.2"
        self.base_url = f"https://api.jablonet.net/api/{api_version}/"
        self.username = username
        self.password = password
        self.pin_code = pin_code

    def set_cookies(self):
        """
        Retrieve the session_id and set it in the header as a cookie
        :return:
        """
        if 'Cookie' in self.headers:
            del self.headers['Cookie']
        session_id = self.get_session_id()
        self.headers['Cookie'] = f'PHPSESSID={session_id}'

    def _make_request(self, end_point: str, headers: dict, payload: dict, retry: int = 0) -> Union[bool, Any]:
        """
        Internal function to handle the parsing of a request to the API
        :param end_point: End point of the API
        :param headers: Header for the request
        :param payload: Body for the request
        :param retry: States whether the request is a retry, only 1 retry is allowed
        :return: Status and the json response
        """
        r = requests.post(
            url=f"{self.base_url}{end_point}",
            headers=self.headers,
            json=payload
        )

        if r.ok:
            data = r.json()
            if end_point == "userAuthorize.json":
                return True, r.cookies.get("PHPSESSID")
            if data.get('data') is not None:
                return True, data["data"]
            else:
                logger.error(f"Unexpected response from API: {data}")
                return False, None

        data = r.json()
        if data.get('http-code', 0) in [400, 401]:
            print(f"Error: {data}, setting cookies and retrying.")
            self.set_cookies()
        else:
            logger.error(f"An unexpected error occurred, status code: {r.status_code}, response: {data}, {r.text}")

        if retry >= 3:
            logger.error(f"Exhausted all retry options, response: {data.json()}")
            if 'errors' in data:
                logger.error(data['errors'])
            return False, None
        else:
            retry += 1
            return self._make_request(end_point=end_point, headers=headers, payload=payload, retry=retry)

    def get_session_id(self) -> str:
        """
        Function to log in to Jablotron and retrieve the session_id which is used in the cookie
        for authentication.
        :return: session_id
        """
        status, data = self._make_request(
            end_point="userAuthorize.json",
            headers=self.headers,
            payload=dict(login=self.username, password=self.password)
        )

        if status:
            return data
        raise UnexpectedResponse("Unable to retrieve session_id.")

    def get_services(self):
        """
        Function returns list or services.

        Example of output:

        [{
            'service-id': 1234567,
            'cloud-entity-id': 'SERVICE_JA100:1234567',
            'name': 'Home',
            'service-type': 'JA100',
            'icon': 'JA100',
            'index': 1000000,
            'level': 'FULL',
            'status': 'ENABLED',
            'visible': True,
            'message': 'OK',
            'event-last-time': '2022-01-01T00:00:00+0200',
            'share-status': 'SHARED',
            'extended-states': [
                {'type': 'ARM', 'value': '0'},
                {'type': 'DISARM', 'value': '1'}
            ]
        },
        {
            'service-id': 2345678,
            ...
        }]
        """
        status, data = self._make_request(
            end_point="serviceListGet.json",
            headers=self.headers,
            payload={"list-type": "EXTENDED", "visibility": "DEFAULT"}
        )

        if status and 'services' in data:
            return data["services"]
        raise UnexpectedResponse("Unable to retrieve services.")

    def get_service_information(self, service_id: int) -> dict:
        """
        Function returns service information about given service_id.

        :param service_id: ID of your service, this ID can be obtained from get_services()

        Example of output:

        {
            "data": {
                "device": {
                    "family": "JA100F",
                    "model-name": "JA-107K",
                    "service-name": "My Home",
                    "registration-key": "12345-12345-ABCD",
                    "firmware": "MD6112.09.1",
                    "registration-date": "2025-01-28T16:56:15+0200"
                },
                "installation-company": {
                    "name": "John Doe",
                    "phone-number": "+420800800522",
                    "email": "john.doe@example.com"
                },
                "support": {
                    "distributor": "JABLOTRON",
                    "phone-number": "+420800800522",
                    "email": "zakaznicka.linka@jablotron.cz"
                }
            },
            "http-code": 200
        }
        """
        status, data = self._make_request(
            end_point="serviceInformationGet.json",
            headers=self.headers,
            payload={"service-id": service_id}
        )
        if status:
            return data
        raise UnexpectedResponse("Unable to retrieve service information.")

    def get_sections(self, service_id: int, service_type: str = "JA100") -> dict:
        """
        Function returns list or section for given service_id.

        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, type can be obtained from output of get_services()

        Example of output:
        [{
            'cloud-component-id': 'SEC-123456789',
            'name': 'Garage',
            'can-control': True,
            'need-authorization': True,
            'partial-arm-enabled': False
        }, {
            'cloud-component-id': 'SEC-234567890',
            ...
        }]
        """
        status, data = self._make_request(
            end_point=f"{service_type}/sectionsGet.json",
            headers=self.headers,
            payload={
                "connect-device": True,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": True
            }
        )
        if status and 'sections' in data:
            return data
        raise UnexpectedResponse("Unable to retrieve sections.")

    def get_thermo_devices(self, service_id: int, service_type: str = "JA100") -> dict:
        """
        Function returns list of thermo devices for given service_id.

        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, default value is "JA100"


        Example of output:
        [{
            'object-device-id': 'THM-123456789',
            'temperature': 20.5,
            'last-temperature-time': '2022-01-01T00:00:00+0200'
        },{
            'object-device-id': 'THM-234567890',
            ...
        }]
        """
        status, data = self._make_request(
            end_point=f"{service_type}/thermoDevicesGet.json",
            headers=self.headers,
            payload={
                "connect-device": True,  # Rather contact device to get actual values.
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": False
            }
        )
        if status and 'states' in data:
            return data['states']
        raise UnexpectedResponse("Unable to retrieve thermo devices.")

    def get_keyboard_segments(self, service_id: int, service_type: str = "JA100") -> dict:
        """
        Function returns list or keyboard segments for given service_id.

        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, type can be obtained from output of get_services()

        Output can contains various fields depending on your keyboard configuration:
        [{
            'object-device-id': 'KBD-123456789',
            'name': 'Entrance',
            'segments': [{'segment-id': 'SEG-123456789',
            'name': '',
            'can-control': False,
            'need-authorization': False,
            'segment-function': 'NONE'
        },{
            'segment-id': 'SEG-123456789',
            'name': 'Garage door',
            'can-control': True,
            'need-authorization': True,
            'display-component-id': 'PG-123456789',
            'control-component-id': 'PG-123456789',
            'segment-function': 'PG_ON_OFF'
        },{
            'segment-id': 'SEG-123456789',
        }]
        """
        status, data = self._make_request(
            end_point=f"{service_type}/keyboardSegmentsGet.json",
            headers=self.headers,
            payload={
                # Probably not necessary to contact device, unless keyboard are often changed/renamed.
                "connect-device": False,
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": False
            }
        )
        if status and 'keyboards' in data:
            return data['keyboards']
        raise UnexpectedResponse("Unable to retrieve keyboards segments")

    def get_programmable_gates(self, service_id: int, service_type: str = "JA100") -> dict:
        """
        Function returns list or PG for given service_id.

        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, type can be obtained from output of get_services()

        Example of output:
        [{
            'cloud-component-id': 'PG-12345678',
            'state': 'OFF'
        },{
            'cloud-component-id': 'PG-23456789',
            ...
        }]
        """
        status, data = self._make_request(
            end_point=f"{service_type}/programmableGatesGet.json",
            headers=self.headers,
            payload={
                "connect-device": True,  # Rather contact device to get actual values.
                "list-type": "FULL",
                "service-id": service_id,
                "service-states": True
            }
        )
        if status:
            return data
        raise UnexpectedResponse("Unable to retrieve programmable gates.")

    def get_service_history(self, service_id: int, date_from: str = "", date_to: str = "", event_id_from: str = "",
                            event_id_to: str = "", service_type: str = "JA100", limit: int = 20) -> dict:
        """
        Function returns list or historical events for given service_id. By default it lists last
        20 events, but this limit can be enlarged and also query can be combined with date_from,
        date_to, event_id_to, event_id_from.

        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, type can be obtained from output of get_services()
        :param limit: Maximal numbers of events that will be returned.
        :param date_from: Optional event filter, events older than date_from will not be returned.
        :param date_to: Optional event filter, events newer than date_to will not be returned.
        :param event_id_from: Optional event filter, events older than event with id=event_id_from will not be returned.
        :param event_id_to: Optional event filter, events newer than event with id=event_id_to will not be returned.

        Example of output:

        [{
            'id': 'OCE-123465789',
            'date': '2022-01-01T00:00:00+0200',
            'icon-type': 'DISARM',
            'event-text': 'Disarmed',
            'section-name': 'Garage',
            'invoker-name': 'John',
            'invoker-type': 'USER'
        },{
            'id': 'OCE-234567890',
            ...
        }]
        """
        payload_json = {
            "limit": limit,
            "service-id": service_id
        }
        if date_from != "":
            payload_json["date-from"] = date_from
        if date_to != "":
            payload_json["date-to"] = date_to
        if event_id_from != "":
            payload_json["event-id-from"] = event_id_from
        if event_id_to != "":
            payload_json["event-id-to"] = event_id_to

        status, data = self._make_request(
            end_point=f"{service_type}/eventHistoryGet.json",
            headers=self.headers,
            payload=payload_json
        )
        if status and 'events' in data:
            return data['events']
        raise UnexpectedResponse("Unable to retrieve event history.")

    def control_component(self, service_id: int, component_id: str, state: str, control_pg: bool = False,
                          service_type: str = "JA100", force: bool = False):
        """
        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param service_type: Type of your service, type can be obtained from output of get_services()
        :param component_id:
        :param control_pg:
        :param state: For a section use either ARM or DISARM, for a PG use ON or OFF
        :param force: Overwrite a blockage of the component
        :return:
        """
        if control_pg is True:
            control_type = "CONTROL-PG"
            if state == "ARM":
                state = "ON"
            elif state == "DISARM":
                state = "OFF"
        else:
            control_type = "CONTROL-SECTION"

        payload_json = {
            "service-id": service_id,
            "authorization": {"authorization-code": f"{self.pin_code}"},
            "control-components": [{
                "actions": dict(action=control_type, value=state.upper()),
                "component-id": component_id,
                "force": force
            }]
        }

        status, data = self._make_request(
            end_point=f"{service_type}/controlComponent.json",
            headers=self.headers,
            payload=payload_json
        )
        if data.get("states") is not None:
            for component in data["states"]:
                if component["component-id"] == component_id and component["state"] == state.upper():
                    return component

        raise UnexpectedResponse(f"Unable to control component, response: {data}")

    def control_programmable_gate(self, service_id: int, component_id: str, on: bool):
        """
        Arm or disarm a programmable gate
        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param component_id: The ID of the section
        :param on: Bool for arming or disarming
        :return:
        """
        if on is True:
            state = "ON"
        else:
            state = "OFF"
        return self.control_component(service_id=service_id, component_id=component_id, state=state, control_pg=True)

    def control_section(self, service_id: int, component_id: str, on: bool):
        """
        Arm or disarm a section
        :param service_id: ID of your service, this ID can be obtained from get_services()
        :param component_id: The ID of the section
        :param on: Bool for arming or disarming
        :return:
        """
        if on is True:
            state = "ARM"
        else:
            state = "DISARM"
        return self.control_component(service_id=service_id, component_id=component_id, state=state)
