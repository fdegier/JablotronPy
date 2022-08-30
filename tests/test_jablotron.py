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
        session_id = self.jablotron.headers["Cookie"].split("=", 1)[1]
        assert len(session_id) == 26
        assert isinstance(session_id, str)

    def test_get_services(self):
        services = self.jablotron.get_services()
        assert isinstance(services, list)
        assert "service-id" in services[0].keys()

    def test_get_sections(self):
        services = self.jablotron.get_services()
        sections = self.jablotron.get_sections(service_id=services[1]["service-id"])
        assert list(sections[0].keys()) == ['cloud-component-id', 'name', 'can-control', 'need-authorization',
                                      'partial-arm-enabled']

