import json
from typing import Union, Any

import requests


class Jablotron:
    def __init__(self, username: str, password: str):
        """
        :param username: Email address used for Jablotron
        :param password: Password used for Jablotron
        """
        self.headers = {
            "x-vendor-id": "MyJABLOTRON"
        }
        api_version = "1.8"
        self.base_url = f"https://api.jablonet.net/api/{api_version}/"
        self.username = username
        self.password = password

    def set_cookies(self):
        """
        Retrieve the session_id and set it in the header as a cookie
        :return:
        """
        session_id = self.get_session_id()
        self.headers['Cookie'] = f'PHPSESSID={session_id}'

    def _make_request(self, end_point, headers, payload, retry=False) -> Union[bool, Any]:
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
            headers=headers,
            data=payload
        )
        if r.ok:
            data = r.json()
            if data["status"] is False and data.get("error_status") == "not_logged_in":
                self.set_cookies()
                if retry:
                    print(f"Exhausted all retry options")
                    return False, None
                else:
                    return self._make_request(end_point=end_point, headers=headers, payload=payload, retry=True)

            return True, r.json()

    def get_session_id(self) -> str:
        """
        Function to log in to Jablotron and retrieve the session_id which is used in the cookie for authentication.
        :return: session_id
        """
        status, data = self._make_request(
            end_point="login.json",
            headers={**self.headers, **{'Content-Type': 'application/x-www-form-urlencoded'}},
            payload=dict(login=self.username, password=self.password)
        )
        if status:
            return data["session_id"]
        raise Exception("Unable to retrieve session_id")

    def get_services(self):
        status, data = self._make_request(
            end_point="getServiceList.json",
            headers=self.headers,
            payload=dict(list_type='extended')
        )
        if status:
            return data["services"]
        raise Exception("Unable to retrieve services")

    def get_service_details(self, service_id: int) -> dict:
        """
        Get details of a service, e.g. segments, keyboards, switches etc.
        :param service_id: Service ID of the Jablotron service
        :return:
        """
        data = {
            "data": json.dumps([{"filter_data": [{"data_type": "section"}, {"data_type": "keyboard"},
                                                 {"data_type": "pgm"}],
                                 "service_type": "ja100",
                                 "service_id": service_id,
                                 "data_group": "serviceData",
                                 "connect": True}])
        }
        status, data = self._make_request(
            end_point="dataUpdate.json",
            headers=self.headers,
            payload=data
        )
        if status:
            return data
        raise Exception("Unable to retrieve details for service")
