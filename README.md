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
| get_service_history       | Returns list of historical events for specified service                      |
| control_section           | Sets specified section of specified service to desired state                 |
| control_programmable_gate | Sets specified programmable gate of specified service to desired state       |
