from typing import TypedDict

# ==================
# ==== SERVICES ====
# ==================

JablotronServiceExtendedState = TypedDict(
    "JablotronServiceExtendedState",
    {
        "type": str,
        "value": str
    }
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
        "extended-states": list[JablotronServiceExtendedState]
    }
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
    }
)

JablotronServiceInformationInstallationCompany = TypedDict(
    "JablotronServiceInformationInstallationCompany",
    {
        "name": str,
        "phone-number": str,
        "email": str
    }
)

JablotronServiceInformationSupport = TypedDict(
    "JablotronServiceInformationSupport",
    {
        "distributor": str,
        "phone-number": str,
        "email": str
    }
)

JablotronServiceInformation = TypedDict(
    "JablotronServiceInformation",
    {
        "device": JablotronServiceInformationDevice,
        "installation-company": JablotronServiceInformationInstallationCompany | None,
        "support": JablotronServiceInformationSupport
    }
)

# ========================
# ==== ALARM SECTIONS ====
# ========================

JablotronSectionsServiceStates = TypedDict(
    "JablotronSectionsServiceStates",
    {
        "service-name": str
    }
)

JablotronSectionsState = TypedDict(
    "JablotronSectionsState",
    {
        "cloud-component-id": str,
        "state": str
    }
)

JablotronSectionsSection = TypedDict(
    "JablotronSectionsSection",
    {
        "cloud-component-id": str,
        "name": str,
        "can-control": bool,
        "need-authorization": bool,
        "partial-arm-enabled": bool
    }
)

JablotronSections = TypedDict(
    "JablotronSections",
    {
        "service-states": JablotronSectionsServiceStates,
        "states": list[JablotronSectionsState],
        "sections": list[JablotronSectionsSection]
    }
)

# ========================
# ==== THERMO DEVICES ====
# ========================

JablotronThermoDevice = TypedDict(
    "JablotronThermoDevice",
    {
        "object-device-id": str,
        "temperature": float,
        "last-temperature-time": str
    }
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
        "segment-function": str
    }
)

JablotronKeyboard = TypedDict(
    "JablotronKeyboard",
    {
        "object-device-id": str,
        "name": str,
        "segments": list[JablotronKeyboardSegment]
    }
)

# ============================
# ==== PROGRAMMABLE GATES ====
# ============================

JablotronProgrammableGatesGate = TypedDict(
    "JablotronProgrammableGatesGate",
    {
        "cloud-component-id": str,
        "name": str,
        "can-control": bool
    }
)

JablotronProgrammableGatesState = TypedDict(
    "JablotronProgrammableGatesState",
    {
        "cloud-component-id": str,
        "state": str
    }
)

JablotronProgrammableGates = TypedDict(
    "JablotronProgrammableGates",
    {
        "programmableGates": list[JablotronProgrammableGatesGate] | None,
        "states": list[JablotronProgrammableGatesState]
    }
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
        "invoker-type": str
    }
)

# =========================
# ==== SECTION CONTROL ====
# =========================

JablotronSectionControlResponseError = TypedDict(
    "JablotronSectionControlResponseError",
    {
        "component-id": str,
        "control-error": str
    }
)

JablotronSectionControlResponseState = TypedDict(
    "JablotronSectionControlResponseState",
    {
        "component-id": str,
        "state": str
    }
)

JablotronSectionControlResponse = TypedDict(
    "JablotronSectionControlResponse",
    {
        "control-errors": list[JablotronSectionControlResponseError] | None,
        "states": list[JablotronSectionControlResponseState]
    }
)

# ===================================
# ==== PROGRAMMABLE GATE CONTROL ====
# ===================================

JablotronProgrammableGateControlResponseError = TypedDict(
    "JablotronProgrammableGateControlResponseError",
    {
        "component-id": str,
        "control-error": str
    }
)

JablotronProgrammableGateControlResponseState = TypedDict(
    "JablotronProgrammableGateControlResponseState",
    {
        "component-id": str,
        "state": str
    }
)

JablotronProgrammableGateControlResponse = TypedDict(
    "JablotronProgrammableGateControlResponse",
    {
        "control-errors": list[JablotronSectionControlResponseError] | None,
        "states": list[JablotronSectionControlResponseState]
    }
)
