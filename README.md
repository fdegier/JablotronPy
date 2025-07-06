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
sections = client.get_sections(service_id=service_id)["sections"]
print(sections)
```

## Methods

The client offers a variation of data, here is a table of the methods and data it returns:

| Method                    | Description |
|---------------------------|-------------|
| control_component         | aaa         |
| control_programmable_gate | TODO:       |
| control_section           | TODO:       |
| get_keyboard_segments     | TODO:       |
| get_programmable_gates    | TODO:       |
| get_sections              | TODO:       |
| get_service_history       | TODO:       |
| get_services              | TODO:       |
| get_session_id            | TODO:       |
| get_thermo_devices        | TODO:       |
| get_service_information   | TODO:       |
