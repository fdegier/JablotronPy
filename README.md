[![PyPI version](https://badge.fury.io/py/jablotronpy.svg)](https://badge.fury.io/py/jablotronpy)

# JablotronPy

Jablotron Cloud API client written in Python that allows you to retrieve data from Jablotron systems as well as control
them.

## Installation

The package is published to [PyPi](https://pypi.org/project/JablotronPy), to install it run the following
command:

```bash
pip install jablotronpy
```

## Usage

This is an example of initializing a client and getting all sections from the first available service:

```python
import os
from jablotronpy.jablotronpy import Jablotron

# Initialize client and perform login
client = Jablotron(
  username=os.environ["JABLOTRON_USER"],
  password=os.environ["JABLOTRON_PASS"],
  pin_code=os.environ["JABLOTRON_PIN"]
)
client.perform_login()

# Get service and its sections
service_id = client.get_services()[0]["service-id"]
sections = client.get_sections(service_id=service_id)
print(sections)
```

Every request to the Jablotron Cloud API gives up after 30 seconds and raises `requests.Timeout`, so a
hanging connection cannot block your application forever. Pass `request_timeout` to `Jablotron(...)` to
change this.

## Methods

The client offers a variation of data, here is a table of the methods and data it returns:

| Method                    | Description                                                                  |
|---------------------------|------------------------------------------------------------------------------|
| perform_login             | Performs initial login to Jablotron Cloud API                                |
| get_services              | Returns list of available services for specified Jablotron Cloud account     |
| get_service_information   | Returns additional information about specified service                       |
| get_sections              | Returns available sections for specified service                             |
| get_thermo_devices        | Returns list of available thermo devices for specified service               |
| get_keyboard_segments     | Returns list of available keyboards and their segments for specified service |
| get_programmable_gates    | Returns available programmable gates and their states for specified service  |
| get_service_history       | Returns list of historical events for specified service (see note below)     |
| get_access_token          | Returns a bearer token for the GraphQL API                                   |
| get_events                | Returns event history (incl. arm/disarm) via the GraphQL API                 |
| get_events_page           | Returns a single page of event history plus a cursor for the next page       |
| control_section           | Sets specified section of specified service to desired state                 |
| control_programmable_gate | Sets specified programmable gate of specified service to desired state       |
| control_thermo_device     | Sets heating mode and/or temperature of specified thermo device              |

## Thermostat control and 502 Bad Gateway

Jablotron Cloud often answers `controlThermoDevice.json` with `502 Bad Gateway` after a few
seconds, while the thermostat still applies the change 20-50 seconds later.
`control_thermo_device` and `control_thermo_device_with_response` therefore treat a 502/504
(or a read timeout) as "not confirmed yet": they poll `get_thermo_devices` every `confirm_interval` seconds
(default `3`) for up to `confirm_timeout` seconds (default `60`) and return as soon as the
thermostat reflects the requested mode/temperature. If it does not, the original
`BadGatewayException` (a subclass of `JablotronApiException`) is raised. Pass
`confirm_timeout=0` to raise immediately instead. Note that the call can block for up to
`confirm_timeout` seconds.

## Detecting active alarms

The Jablotron Cloud API does not push notifications to third-party clients, so detecting an
active alarm requires polling. The signal lives in the `sectionsGet` response, **not** in
`serviceListGet` or in the section state itself (a section in alarm continues to report state
`ARM`). While an alarm is live, `data["service-states"]` contains an `events` list:

```json
{
  "service-states": {
    "service-name": "Home",
    "events": [
      {
        "type": "ALARM",
        "message": "Alarm - Periphery PIR hallway (wifi), Section House",
        "date": "2026-04-26T10:24:16+0200"
      }
    ]
  },
  "states": [{"cloud-component-id": "SEC-...", "state": "ARM"}],
  "sections": [...]
}
```

Notes:

- The `events` key is **only present while an event is active**. If the alarm ends before
  the next poll, you will miss it.
- Observed `type` value: `"ALARM"`. Other types (tamper, sabotage, fault) likely exist but
  are not yet documented here.
- The `JA100/eventHistoryGet.json` endpoint exposed via `get_service_history` now returns
  `400 METHOD.NOT-SUPPORTED` regardless of parameters, for every panel type. Use
  `get_events` instead (see below).

Minimal poller:

```python
sections = client.get_sections(service_id=sid)
for event in sections["service-states"].get("events", []):
    if event["type"] == "ALARM":
        ...  # handle alarm
```

## Event history (arm/disarm, etc.)

`get_service_history` (the `eventHistoryGet.json` REST endpoint) has stopped working. The
official app instead fetches event history through a separate GraphQL API
(`https://graph.jablotron.cloud/graphql`), authenticated with a short-lived bearer token.
`get_events` implements that flow and returns the same kind of data (including which
section was armed/disarmed, by whom, and when):

```python
service = client.get_services()[0]
events = client.get_events(service_id=service["service-id"], service_type=service["service-type"])
for event in events:
    if event["type"] in ("SECURITY_SYSTEM.CONTROL.SECTION_ARM", "SECURITY_SYSTEM.CONTROL.SECTION_DISARM"):
        section = next((s["name"] for s in event["subjects"]), None)
        invoker = next((i["name"] for i in event["invokers"]), None)
        print(event["occurredAt"], event["type"], section, invoker)
```

Notes:

- `service_type` is required here and must be the panel type from the `service-type`
  value of `get_services()` (e.g. `JA100F`). It is used to build the GraphQL entity id
  and is unrelated to the `service_type` parameter on the REST endpoints (which defaults
  to `JA100`).
- The API rejects page sizes above roughly 20-24 (`Request validation failed` with no
  further detail), so `page_size` is limited to 20 and `get_events` paginates internally.
  It stops after `max_pages` pages (default `10`, i.e. up to 200 events); pass
  `max_pages=None` for the complete history, or use `get_events_page` and its
  `end-cursor` to paginate yourself.
- The bearer token is cached and renewed automatically. `get_access_token` can be
  called on its own if you need to talk to the GraphQL API directly for something this
  library doesn't wrap yet.
