"""Types for Jablotron API integration."""

from typing import TypedDict

# ==================
# ==== SERVICES ====
# ==================

JablotronServiceExtendedState = TypedDict(
    "JablotronServiceExtendedState",
    {
        "type": str,
        "value": str,
    },
)

JablotronService = TypedDict(
    "JablotronService",
    {
        "service-id": int,
        "cloud-entity-id": str,
        "name": str,
        "service-type": str,
        "icon": str,
        "index": int,
        "level": str,
        "status": str,
        "visible": bool,
        "message": str,
        "event-last-time": str,
        "share-status": str,
        "extended-states": list[JablotronServiceExtendedState],
    },
)

# =============================
# ==== SERVICE INFORMATION ====
# =============================

JablotronServiceInformationDevice = TypedDict(
    "JablotronServiceInformationDevice",
    {
        "family": str,
        "model-name": str,
        "service-name": str,
        "registration-key": str,
        "registration-date": str,
        "phone-number": str,
        "firmware": str,
    },
)

JablotronServiceInformationInstallationCompany = TypedDict(
    "JablotronServiceInformationInstallationCompany",
    {
        "name": str,
        "phone-number": str,
        "email": str,
    },
)

JablotronServiceInformationSupport = TypedDict(
    "JablotronServiceInformationSupport",
    {
        "distributor": str,
        "phone-number": str,
        "email": str,
    },
)

JablotronServiceInformation = TypedDict(
    "JablotronServiceInformation",
    {
        "device": JablotronServiceInformationDevice,
        "installation-company": JablotronServiceInformationInstallationCompany | None,
        "support": JablotronServiceInformationSupport,
    },
)

# ========================
# ==== ALARM SECTIONS ====
# ========================

JablotronSectionsServiceStates = TypedDict(
    "JablotronSectionsServiceStates",
    {
        "service-name": str,
    },
)

JablotronSectionsState = TypedDict(
    "JablotronSectionsState",
    {
        "cloud-component-id": str,
        "state": str,
    },
)

JablotronSectionsSection = TypedDict(
    "JablotronSectionsSection",
    {
        "cloud-component-id": str,
        "name": str,
        "can-control": bool,
        "need-authorization": bool,
        "partial-arm-enabled": bool,
    },
)

JablotronSections = TypedDict(
    "JablotronSections",
    {
        "service-states": JablotronSectionsServiceStates,
        "states": list[JablotronSectionsState],
        "sections": list[JablotronSectionsSection],
    },
)

# ========================
# ==== THERMO DEVICES ====
# ========================

JablotronThermoDeviceDetails = TypedDict(
    "JablotronThermoDeviceDetails",
    {
        "object-device-id": str,
        "cloud-entity-id": str,
        "name": str,
        "can-control": bool,
        "can-show-graph": bool,
        "unit": str,
        "type": str,
        "temperature-range-min": float,
        "temperature-range-max": float,
    },
)

JablotronThermoDeviceState = TypedDict(
    "JablotronThermoDeviceState",
    {
        "object-device-id": str,
        "temperature": float,
        "last-temperature-time": str,
        "temperature-set": float,
        "mode": str,
        "temperature-comfort": float,
        "temperature-economic": float,
        "next-temperature-change": str,
        "next-temperature-mode": str,
        "heating-state": str,
    },
)

JablotronThermoDevice = TypedDict(
    "JablotronThermoDevice",
    {
        "object-device-id": str,
        "name": str,
        "temperature": float,
        "last-temperature-time": str,
        "thermo-device": JablotronThermoDeviceDetails,
        "state": JablotronThermoDeviceState,
    },
)

# ===========================
# ==== KEYBOARD SEGMENTS ====
# ===========================

JablotronKeyboardSegment = TypedDict(
    "JablotronKeyboardSegment",
    {
        "segment-id": str,
        "name": str,
        "can-control": bool,
        "need-authorization": bool,
        "display-component-id": str | None,
        "control-component-id": str | None,
        "segment-function": str,
    },
)

JablotronKeyboard = TypedDict(
    "JablotronKeyboard",
    {
        "object-device-id": str,
        "name": str,
        "segments": list[JablotronKeyboardSegment],
    },
)

# ============================
# ==== PROGRAMMABLE GATES ====
# ============================

JablotronProgrammableGatesGate = TypedDict(
    "JablotronProgrammableGatesGate",
    {
        "cloud-component-id": str,
        "name": str,
        "can-control": bool,
    },
)

JablotronProgrammableGatesState = TypedDict(
    "JablotronProgrammableGatesState",
    {
        "cloud-component-id": str,
        "state": str,
    },
)

JablotronProgrammableGates = TypedDict(
    "JablotronProgrammableGates",
    {
        "programmableGates": list[JablotronProgrammableGatesGate] | None,
        "states": list[JablotronProgrammableGatesState],
    },
)

# =========================
# ==== SERVICE HISTORY ====
# =========================

JablotronServiceHistoryEvent = TypedDict(
    "JablotronServiceHistoryEvent",
    {
        "id": str,
        "date": str,
        "icon-type": str,
        "event-text": str,
        "section-name": str,
        "invoker-name": str,
        "invoker-type": str,
    },
)

# =========================
# ==== SECTION CONTROL ====
# =========================

JablotronSectionControlResponseError = TypedDict(
    "JablotronSectionControlResponseError",
    {
        "component-id": str,
        "control-error": str,
    },
)

JablotronSectionControlResponseState = TypedDict(
    "JablotronSectionControlResponseState",
    {
        "component-id": str,
        "state": str,
    },
)

JablotronSectionControlResponse = TypedDict(
    "JablotronSectionControlResponse",
    {
        "control-errors": list[JablotronSectionControlResponseError] | None,
        "states": list[JablotronSectionControlResponseState],
    },
)

# ===================================
# ==== PROGRAMMABLE GATE CONTROL ====
# ===================================

JablotronProgrammableGateControlResponseError = TypedDict(
    "JablotronProgrammableGateControlResponseError",
    {
        "component-id": str,
        "control-error": str,
    },
)

JablotronProgrammableGateControlResponseState = TypedDict(
    "JablotronProgrammableGateControlResponseState",
    {
        "component-id": str,
        "state": str,
    },
)

JablotronProgrammableGateControlResponse = TypedDict(
    "JablotronProgrammableGateControlResponse",
    {
        "control-errors": list[JablotronSectionControlResponseError] | None,
        "states": list[JablotronSectionControlResponseState],
    },
)

# =========================
# ==== DEVICE SCHEDULE ====
# =========================

JablotronDeviceScheduleDataEntry = TypedDict(
    "JablotronDeviceScheduleDataEntry",
    {
        "id": str,
        "value": str,
        "day": str,
        "start": int,
        "end": int,
    },
)

JablotronDeviceScheduleEntry = TypedDict(
    "JablotronDeviceScheduleEntry",
    {
        "room_id": str,
        "programs": list[str],
        "group_by": str,
        "default": str,
        "restrict_count": int,
        "restrict_count_interval": str,
        "data": list[JablotronDeviceScheduleDataEntry],
    },
)

JablotronDeviceSchedule = TypedDict(
    "JablotronDeviceSchedule",
    {
        "id": str,
        "type": str,
        "parent_id": int,
        "parent_type": str,
        "schedule": list[JablotronDeviceScheduleEntry],
        "status": bool,
        "checksum": str,
        "server_id": str,
        "client_id": str | None,
    },
)

# ==========================
# ==== SERVICE SETTINGS ====
# ==========================

JablotronServiceInformationDevice = TypedDict(
    "JablotronServiceInformationDevice",
    {
        "family": str,
        "model-name": str,
        "service-name": str,
        "registration-key": str,
        "registration-date": str,
        "phone-number": str,
        "firmware": str,
    },
)

JablotronServiceInformationInstallationCompany = TypedDict(
    "JablotronServiceInformationInstallationCompany",
    {
        "name": str,
        "phone-number": str,
        "email": str,
    },
)

JablotronServiceSettingsNamesEntry = TypedDict(
    "JablotronServiceSettingsNamesEntry",
    {
        "name_type": str,
        "name_key": str,
        "name_value": str,
    },
)

JablotronServiceSettingsThermostatSettingsPrograms = TypedDict(
    "JablotronServiceSettingsThermostatSettingsPrograms",
    {
        "temp_economy": float,
        "temp_comfort": float,
        "temp_turned_off": float,
    },
)

JablotronServiceSettingsThermostatSettings = TypedDict(
    "JablotronServiceSettingsThermostatSettings",
    {
        "temperature_limits_editable": bool,
        "hysteresis": float,
        "calibration_offset": float,
        "temp_min": float,
        "temp_max": float,
        "programs": JablotronServiceSettingsThermostatSettingsPrograms,
    },
)

JablotronServiceSettingsThermostatsEntry = TypedDict(
    "JablotronServiceSettingsThermostatsEntry",
    {
        "object_id": str,
        "thermostat_index": str,
        "object-device-id": str,
        "thermostat_name": str,
        "type": str,
        "settings": JablotronServiceSettingsThermostatSettings,
    },
)

JablotronServiceSettings = TypedDict(
    "JablotronServiceSettings",
    {
        "status": bool,
        "settings_service_index": int,
        "settings_service_visible": bool,
        "settings_change_registration": bool,
        "settings_names": list[JablotronServiceSettingsNamesEntry],
        "permissions": None,
        "settings_lite_plus_allowed": bool,
        "thermostats": list[JablotronServiceSettingsThermostatsEntry],
        "checksum": str,
        "server_id": str,
        "client_id": str | None,
    },
)

JablotronServiceSettingsUpdateResponse = TypedDict(
    "JablotronServiceSettingsUpdateResponse",
    {
        "status": bool,
        "checksum": str,
        "server_id": str,
        "client_id": str | None,
        "error_status": str | None,
        "error_message": str | None,
    },
)
