[![PyPI version](https://badge.fury.io/py/jablotronpy.svg)](https://badge.fury.io/py/jablotronpy)
# JablotronPy

Due to popular request, work has started on a Jablotron client for Python that will be used to
write a Jablotron plugin for Home Assistant. It will also be used in a simple gui that 
will help people setup their Homebridge config. 

## Installation

The package is published to [PyPi](https://pypi.org/project/JablotronPy/0.4.0/), to install it run the following 
command:
```bash
pip install jablotronpy
```

## Usage

Below is an example of authenticating and getting all sections.

```python
import os
from jablotronpy.jablotronpy import Jablotron

j = Jablotron(username=os.environ["JABLOTRON_USER"], 
              password=os.environ["JABLOTRON_PASS"], 
              pin_code=os.environ["JABLOTRON_PIN"])

service_id = j.get_services()[0]["service-id"]
print(j.get_sections(service_id=service_id)["sections"])
```

## Methods

The following methods are available:
- control_component
- control_programmable_gate
- control_section
- get_keyboard_segments
- get_programmable_gates
- get_sections
- get_service_history
- get_services
- get_session_id
- get_thermo_devices
