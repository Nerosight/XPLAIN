"""SDDL (Security Descriptor Definition Language) string parser.

SDDL strings are returned by tools like `sc sdshow`, `icacls`, `Get-Acl`, and
the Windows registry. They describe a security descriptor as four optional
sections: O: (owner), G: (group), D: (DACL), S: (SACL).

The DACL and SACL contain ACEs of the form:
    (ace_type;ace_flags;rights;object_guid;inherit_object_guid;account_sid)

This parser currently uses **service-object** context for the rights field.
The same two-letter codes (CC, LC, SW, ...) mean different things on files,
registry keys, and AD objects - that's a roadmap item.

Reference: Microsoft "Security Descriptor String Format" docs and winnt.h.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from xplain.core.base import Annotation, Parser


# ACE types (first field of an ACE).
_ACE_TYPES = {
    "A":  ("ACCESS_ALLOWED",            "Allows the trustee the specified rights."),
    "D":  ("ACCESS_DENIED",             "Denies the trustee the specified rights."),
    "OA": ("OBJECT_ACCESS_ALLOWED",     "Object-specific allow ACE (uses object/inherit GUIDs)."),
    "OD": ("OBJECT_ACCESS_DENIED",      "Object-specific deny ACE."),
    "AU": ("SYSTEM_AUDIT",              "Audit ACE: logs access attempts (see flags for SA/FA)."),
    "AL": ("SYSTEM_ALARM",              "Alarm ACE (reserved/unused on Windows)."),
    "OU": ("SYSTEM_OBJECT_AUDIT",       "Object-specific audit ACE."),
    "OL": ("SYSTEM_OBJECT_ALARM",       "Object-specific alarm ACE."),
    "ML": ("SYSTEM_MANDATORY_LABEL",    "Mandatory integrity level label."),
    "XA": ("ACCESS_ALLOWED_CALLBACK",   "Callback allow ACE (conditional expression)."),
    "XD": ("ACCESS_DENIED_CALLBACK",    "Callback deny ACE."),
    "RA": ("SYSTEM_RESOURCE_ATTRIBUTE", "Resource attribute ACE."),
    "SP": ("SYSTEM_SCOPED_POLICY_ID",   "Central access policy ID ACE."),
    "XU": ("SYSTEM_AUDIT_CALLBACK",     "Callback audit ACE."),
    "ZA": ("ACCESS_ALLOWED_CALLBACK_OBJECT", "Callback object allow ACE."),
}

# ACE flags (second field). Any number, two chars each.
_ACE_FLAGS = {
    "CI": ("CONTAINER_INHERIT",       "ACE is inherited by child containers."),
    "OI": ("OBJECT_INHERIT",          "ACE is inherited by child objects."),
    "NP": ("NO_PROPAGATE_INHERIT",    "Inherited ACE does not propagate further."),
    "IO": ("INHERIT_ONLY",            "ACE applies only to inheritors, not this object."),
    "ID": ("INHERITED",               "ACE was inherited from a parent."),
    "SA": ("SUCCESSFUL_ACCESS",       "Audit successful access (audit/alarm ACEs)."),
    "FA": ("FAILED_ACCESS",           "Audit failed access (audit/alarm ACEs)."),
    "TL": ("TRUST_PROTECTED_FILTER",  "Trust label filter (less common)."),
    "CR": ("CRITICAL",                "Critical ACE (less common)."),
}

# Service-context rights. The same two-letter codes mean different things on
# files / registry / AD objects - see this module's docstring.
_SERVICE_RIGHTS = {
    # Generic / standard rights (universal)
    "GA": ("GENERIC_ALL",         "All possible access rights."),
    "GR": ("GENERIC_READ",        "Generic read."),
    "GW": ("GENERIC_WRITE",       "Generic write."),
    "GX": ("GENERIC_EXECUTE",     "Generic execute."),
    "RC": ("READ_CONTROL",        "Read the security descriptor (except SACL)."),
    "SD": ("DELETE",              "Delete the object."),
    "WD": ("WRITE_DAC",           "Modify the DACL."),
    "WO": ("WRITE_OWNER",         "Take ownership."),
    # Service-specific (SERVICE_*)
    "CC": ("SERVICE_QUERY_CONFIG",         "Query the service configuration."),
    "DC": ("SERVICE_CHANGE_CONFIG",        "Change the service configuration."),
    "LC": ("SERVICE_QUERY_STATUS",         "Query the current status of the service."),
    "SW": ("SERVICE_ENUMERATE_DEPENDENTS", "Enumerate the service's dependents."),
    "RP": ("SERVICE_START",                "Start the service."),
    "WP": ("SERVICE_STOP",                 "Stop the service."),
    "DT": ("SERVICE_PAUSE_CONTINUE",       "Pause or continue the service."),
    "LO": ("SERVICE_INTERROGATE",          "Send an interrogate control to the service."),
    "CR": ("SERVICE_USER_DEFINED_CONTROL", "Send a user-defined control code to the service."),
}

# Well-known SIDs (last field of an ACE). Subset of the standard set.
_WELL_KNOWN_SIDS = {
    "AN": ("Anonymous Logon",                 "Anonymous logon."),
    "AO": ("Account Operators",               "Built-in Account Operators group."),
    "AU": ("Authenticated Users",             "All users authenticated by some authority."),
    "BA": ("Built-in Administrators",         "Built-in Administrators group."),
    "BG": ("Built-in Guests",                 "Built-in Guests group."),
    "BO": ("Backup Operators",                "Built-in Backup Operators group."),
    "BU": ("Built-in Users",                  "Built-in Users group."),
    "CA": ("Cert Publishers",                 "Domain Cert Publishers group."),
    "CD": ("Certificate Service DCOM Access", "Certificate Service DCOM Access group."),
    "CG": ("Creator Group",                   "Creator group placeholder SID."),
    "CO": ("Creator Owner",                   "Creator owner placeholder SID."),
    "DA": ("Domain Admins",                   "Domain Administrators group."),
    "DC": ("Domain Computers",                "Domain Computers group."),
    "DD": ("Domain Controllers",              "Domain Controllers group."),
    "DG": ("Domain Guests",                   "Domain Guests group."),
    "DU": ("Domain Users",                    "Domain Users group."),
    "EA": ("Enterprise Admins",               "Enterprise Administrators group."),
    "ED": ("Enterprise Domain Controllers",   "Enterprise Domain Controllers group."),
    "IU": ("Interactive Users",               "Users logged in interactively."),
    "LA": ("Local Administrator",             "Local administrator account."),
    "LG": ("Local Guest",                     "Local guest account."),
    "LS": ("Local Service",                   "Local Service account."),
    "NO": ("Network Configuration Operators", "Network Configuration Operators group."),
    "NS": ("Network Service",                 "Network Service account."),
    "NU": ("Network Logon Users",             "Users logged in over the network."),
    "PA": ("Group Policy Admins",             "Group Policy Administrators."),
    "PO": ("Printer Operators",               "Built-in Printer Operators group."),
    "PS": ("Self",                            "The principal itself (PRINCIPAL_SELF)."),
    "PU": ("Power Users",                     "Built-in Power Users group."),
    "RC": ("Restricted Code",                 "Restricted code SID (note: same code as the READ_CONTROL right)."),
    "RD": ("Remote Desktop Users",            "Remote Desktop Users group."),
    "RE": ("Replicator",                      "Built-in Replicator group."),
    "RO": ("Enterprise Read-only DCs",        "Enterprise Read-only Domain Controllers."),
    "RS": ("RAS Servers",                     "RAS and IAS Servers group."),
    "RU": ("Pre-Windows 2000 Compat Access",  "Pre-Windows 2000 Compatible Access group."),
    "SA": ("Schema Admins",                   "Schema Administrators."),
    "SI": ("System Integrity",                "Integrity level System."),
    "SO": ("Server Operators",                "Built-in Server Operators group."),
    "SU": ("Service Users",                   "All service-logon users."),
    "SY": ("Local System",                    "The Local System account (NT AUTHORITY\\SYSTEM)."),
    "WD": ("Everyone",                        "World / Everyone (note: same code as the WRITE_DAC right)."),
    "OW": ("Owner Rights",                    "OWNER RIGHTS principal."),
    "MU": ("Performance Monitor Users",       "Performance Monitor Users."),
    "LU": ("Performance Log Users",           "Performance Log Users."),
}

# DACL/SACL flags appearing between the section letter and the first ACE.
_ACL_FLAGS = {
    "P":  ("PROTECTED",        "Protected: parent ACEs do not flow into this ACL."),
    "AR": ("AUTO_INHERIT_REQ", "Auto-inherit required."),
    "AI": ("AUTO_INHERITED",   "Auto-inherited."),
}

_SECTION_LABELS = {
    "O:": ("Owner", "Owner SID section."),
    "G:": ("Group", "Primary group SID section."),
    "D:": ("DACL",  "Discretionary Access Control List - who can do what."),
    "S:": ("SACL",  "System Access Control List - what to audit."),
}

_SECTION_RE = re.compile(r"[OGDS]:")


class SddlParser(Parser):
    name = "sddl"
    description = "Windows SDDL strings (default: service-object context for rights)."
    example = "D:(A;;CCLCSWRPLORC;;;AU)"

    def parse(self, text: str) -> Iterable[Annotation]:
        sections = self._split_sections(text)
        for kind, marker_off, body_start, body_end in sections:
            label, desc = _SECTION_LABELS[kind]
            yield Annotation(
                marker_off, marker_off + 2, f"{label} section", kind, desc, "section"
            )
            if kind in ("D:", "S:"):
                yield from self._parse_acl(text, body_start, body_end)
            else:
                yield from self._parse_sid(text[body_start:body_end], body_start)

    # ------------------------------------------------------------------
    # section splitting
    # ------------------------------------------------------------------

    def _split_sections(self, text: str) -> List[Tuple[str, int, int, int]]:
        """Return (kind, marker_offset, body_start, body_end) per section."""
        markers = [(m.start(), m.group()) for m in _SECTION_RE.finditer(text)]
        if not markers:
            raise ValueError("no SDDL section found (expected one of O:, G:, D:, S:)")
        out = []
        for i, (off, kind) in enumerate(markers):
            body_start = off + 2
            body_end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
            out.append((kind, off, body_start, body_end))
        return out

    # ------------------------------------------------------------------
    # ACL parsing
    # ------------------------------------------------------------------

    def _parse_acl(self, text: str, start: int, end: int) -> Iterable[Annotation]:
        first_paren = text.find("(", start, end)
        flags_end = first_paren if first_paren != -1 else end
        if flags_end > start:
            yield from self._parse_acl_flags(text, start, flags_end)

        i = first_paren
        while i != -1 and i < end:
            close = text.find(")", i, end)
            if close == -1:
                raise ValueError(f"unclosed ACE starting at position {i}")
            yield Annotation(i, i + 1, "ACE start", "(", "Begin ACE.", "delimiter")
            yield from self._parse_ace(text, i + 1, close)
            yield Annotation(close, close + 1, "ACE end", ")", "End ACE.", "delimiter")
            i = text.find("(", close + 1, end)

    def _parse_acl_flags(self, text: str, start: int, end: int) -> Iterable[Annotation]:
        i = start
        while i < end:
            matched = False
            # Try multi-char flags before single-char flags.
            for flag in ("AR", "AI", "P"):
                if text.startswith(flag, i) and i + len(flag) <= end:
                    label, desc = _ACL_FLAGS[flag]
                    yield Annotation(i, i + len(flag), label, flag, desc, "ace_flag")
                    i += len(flag)
                    matched = True
                    break
            if not matched:
                i += 1  # unknown char - skip silently for now

    # ------------------------------------------------------------------
    # ACE parsing
    # ------------------------------------------------------------------

    def _parse_ace(self, text: str, start: int, end: int) -> Iterable[Annotation]:
        """Parse one ACE body (between '(' and ')')."""
        # Split into fields by ';' while preserving offsets.
        fields: List[Tuple[int, int, str]] = []
        field_start = start
        for i in range(start, end):
            if text[i] == ";":
                fields.append((field_start, i, text[field_start:i]))
                field_start = i + 1
        fields.append((field_start, end, text[field_start:end]))

        # Mark ';' separators (rendered dim, hidden in legend).x`
        for fs, fe, _ in fields[:-1]:
            yield Annotation(fe, fe + 1, ";", ";", "field separator", "delimiter")

        # Standard SDDL ACE field order.
        roles = [
            "ace_type",
            "ace_flags",
            "rights",
            "object_guid",
            "inherit_guid",
            "sid",
            "resource_attr",
        ]
        for i, (fs, _fe, value) in enumerate(fields):
            if not value:
                continue
            role = roles[i] if i < len(roles) else "extra"
            if role == "ace_type":
                yield from self._annotate_ace_type(value, fs)
            elif role == "ace_flags":
                yield from self._annotate_ace_flags(value, fs)
            elif role == "rights":
                yield from self._annotate_rights(value, fs)
            elif role == "sid":
                yield from self._parse_sid(value, fs)
            elif role in ("object_guid", "inherit_guid"):
                yield Annotation(
                    fs, fs + len(value), role.replace("_", " "), value,
                    f"{role.replace('_', ' ').capitalize()}: {value}", "guid",
                )

    def _annotate_ace_type(self, code: str, offset: int) -> Iterable[Annotation]:
        if code in _ACE_TYPES:
            label, desc = _ACE_TYPES[code]
            yield Annotation(offset, offset + len(code), label, code, desc, "ace_type")
        else:
            yield Annotation(
                offset, offset + len(code),
                f"Unknown ACE type {code!r}", code,
                "Unrecognized ACE type code.", "ace_type",
            )

    def _annotate_ace_flags(self, value: str, offset: int) -> Iterable[Annotation]:
        for i in range(0, len(value), 2):
            chunk = value[i : i + 2]
            if chunk in _ACE_FLAGS:
                label, desc = _ACE_FLAGS[chunk]
                yield Annotation(offset + i, offset + i + 2, label, chunk, desc, "ace_flag")
            else:
                yield Annotation(
                    offset + i, offset + i + len(chunk),
                    f"Unknown flag {chunk!r}", chunk,
                    "Unrecognized ACE flag.", "ace_flag",
                )

    def _annotate_rights(self, value: str, offset: int) -> Iterable[Annotation]:
        if value.lower().startswith("0x"):
            yield Annotation(
                offset, offset + len(value),
                f"Rights mask {value}", value,
                f"Access mask as hex: {value}.", "access_right",
            )
            return
        for i in range(0, len(value), 2):
            chunk = value[i : i + 2]
            if chunk in _SERVICE_RIGHTS:
                label, desc = _SERVICE_RIGHTS[chunk]
                yield Annotation(
                    offset + i, offset + i + 2, label, chunk, desc, "access_right"
                )
            else:
                yield Annotation(
                    offset + i, offset + i + len(chunk),
                    f"Unknown right {chunk!r}", chunk,
                    "Unrecognized right code (service context).", "access_right",
                )

    def _parse_sid(self, value: str, offset: int) -> Iterable[Annotation]:
        value = value.strip()
        if not value:
            return
        if value in _WELL_KNOWN_SIDS:
            label, desc = _WELL_KNOWN_SIDS[value]
            yield Annotation(offset, offset + len(value), label, value, desc, "principal")
        else:
            yield Annotation(
                offset, offset + len(value),
                f"SID {value}", value,
                "Security identifier (raw SID or unrecognized short code).", "principal",
            )
