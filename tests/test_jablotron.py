import os
from unittest import TestCase

from jablotronpy.jablotronpy import Jablotron


class TestJablotron(TestCase):
    jablotron = Jablotron(username=os.environ["TEST_JABLOTRON_USER"], password=os.environ["TEST_JABLOTRON_PASS"])

    def test_set_cookies(self):
        self.jablotron.set_cookies()
        cookie = self.jablotron.headers["Cookie"]
        assert cookie.startswith("PHPSESSID=")

    def test_get_session_id(self):
        session_id = self.jablotron.get_session_id()
        assert len(session_id) == 26
        assert isinstance(session_id, str)

    def test_get_services(self):
        services = self.jablotron.get_services()
        assert isinstance(services, list)
        assert "id" in services[0].keys()

    def test_get_service_details(self):
        service_details = self.jablotron.get_service_details(self.jablotron.get_services()[0]["id"])
        assert isinstance(service_details, dict)
        assert "service_data" in service_details["data"].keys()
