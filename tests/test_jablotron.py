import os
from unittest import TestCase

from jablotronpy.jablotronpy import Jablotron


class TestJablotron(TestCase):
    jablotron = Jablotron(username=os.environ["TEST_JABLOTRON_USER"], password=os.environ["TEST_JABLOTRON_PASS"],
                          pin_code=os.environ["TEST_JABLOTRON_PIN"])

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
        assert list(sections.keys()) == ['service-states', 'states', 'sections']

    def test_get_programmable_gates(self):
        services = self.jablotron.get_services()
        sections = self.jablotron.get_programmable_gates(service_id=services[1]["service-id"])
        assert list(sections.keys()) == ['service-states', 'states', 'programmableGates']

    def test_control_programmable_gate(self):
        service_id = self.jablotron.get_services()[1]["service-id"]
        pg_id = self.jablotron.get_programmable_gates(service_id=service_id)["states"][15]["cloud-component-id"]
        data = self.jablotron.control_programmable_gate(service_id=service_id, component_id=pg_id, on=False)
        assert data["component-id"] == pg_id
        assert data["state"] == "OFF"
