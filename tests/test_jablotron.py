import os
from unittest import TestCase, skip

from jablotronpy.jablotronpy import Jablotron


class TestJablotron(TestCase):
    # Initialize client and perform initial login
    jablotron = Jablotron(
        username=os.environ["TEST_JABLOTRON_USER"],
        password=os.environ["TEST_JABLOTRON_PASS"],
        pin_code=os.environ["TEST_JABLOTRON_PIN"],
    )
    jablotron.perform_login()

    def test_session_id(self):
        """Validate that login function works."""

        cookie = self.jablotron._headers["Cookie"]
        session_id = cookie.split("=", 1)[1]

        assert cookie.startswith("PHPSESSID=")
        assert len(session_id) == 26
        assert isinstance(session_id, str)

    def test_get_services(self):
        """Validate that get_services function works."""

        services = self.jablotron.get_services()

        assert isinstance(services, list)
        assert "service-id" in services[0].keys()

    def test_get_service_information(self):
        """Validate that get_service_information function works."""

        services = self.jablotron.get_services()
        information = self.jablotron.get_service_information(service_id=services[0]["service-id"])

        # Do NOT validate 'installation-company' property since it's optional in the response
        assert list(information.keys()) == ["device", "support"]

    def test_get_sections(self):
        """Validate that get_sections function works."""

        services = self.jablotron.get_services()
        sections = self.jablotron.get_sections(service_id=services[0]["service-id"])

        assert list(sections.keys()) == ["service-states", "states", "sections"]

    def test_get_thermo_devices(self):
        """Validate that get_thermo_devices function works."""

        services = self.jablotron.get_services()
        thermo_devices = self.jablotron.get_thermo_devices(service_id=services[0]["service-id"])

        assert isinstance(thermo_devices, list)

    def test_get_keyboard_segments(self):
        """Validate that get_keyboard_segments function works."""

        services = self.jablotron.get_services()
        keyboards = self.jablotron.get_keyboard_segments(
            service_id=services[0]["service-id"]
        )

        assert list(keyboards[0].keys()) == ["object-device-id", "name", "segments"]

    def test_get_programmable_gates(self):
        """Validate that get_programmable_gates function works."""

        services = self.jablotron.get_services()
        sections = self.jablotron.get_programmable_gates(
            service_id=services[0]["service-id"]
        )

        # Do NOT validate 'programmableGates' property since it's optional in the response
        assert list(sections.keys()) == ["service-states", "states"]

    @skip("Function is not supported - for me only?")
    def test_get_service_history(self):
        """Validate that get_service_history function works."""

        services = self.jablotron.get_services()
        events = self.jablotron.get_service_history(
            service_id=services[0]["service-id"]
        )

        assert list(events[0].keys()) == [
            "id",
            "date",
            "icon-type",
            "event-text",
            "section-name",
            "invoker-name",
            "invoker-type"
        ]

    def test_control_section(self):
        """Validate that control_section function works."""

        services = self.jablotron.get_services()
        sections = self.jablotron.get_sections(service_id=services[0]["service-id"])
        action_successful = self.jablotron.control_section(
            service_id=services[0]["service-id"],
            component_id=sections["sections"][1]["cloud-component-id"],
            state="DISARM"
        )

        assert action_successful is True

    @skip("Test only if developer has PGs in their system!")
    def test_control_programmable_gate(self):
        """Validate that control_programmable_gate function works."""

        services = self.jablotron.get_services()
        gates = self.jablotron.get_programmable_gates(service_id=services[0]["service-id"])
        action_successful = self.jablotron.control_programmable_gate(
            service_id=services[0]["service-id"],
            component_id=gates["states"][1]["cloud-component-id"],
            state="OFF"
        )

        assert action_successful is True
