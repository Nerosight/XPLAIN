"""Tests for the SDDL parser, including the HTB wuauserv example."""

from __future__ import annotations

from xplain.parsers.sddl import SddlParser


HTB_EXAMPLE = (
    "D:(A;;CCLCSWRPLORC;;;AU)"
    "(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)"
    "(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;SY)"
    "S:(AU;FA;CCDCLCSWRPWPDTLOSDRCWDWO;;;WD)"
)


def _parse(text):
    return list(SddlParser().parse(text))


def _by_label(anns, label):
    return [a for a in anns if a.label == label]


def test_htb_example_finds_dacl_and_sacl():
    anns = _parse(HTB_EXAMPLE)
    sections = [a for a in anns if a.category == "section"]
    assert any(a.short_code == "D:" for a in sections)
    assert any(a.short_code == "S:" for a in sections)


def test_htb_example_first_ace_rights():
    """First ACE rights = CCLCSWRPLORC -> 6 service rights, in order."""
    anns = _parse(HTB_EXAMPLE)
    rights = [a for a in anns if a.category == "access_right"]
    # First ACE rights start at offset 5 ('CCLCSWRPLORC' begins after 'D:(A;;')
    first_ace_rights = [a for a in rights if a.start < 17]
    codes = [a.short_code for a in first_ace_rights]
    assert codes == ["CC", "LC", "SW", "RP", "LO", "RC"]


def test_htb_example_principals():
    anns = _parse(HTB_EXAMPLE)
    principals = [a.short_code for a in anns if a.category == "principal"]
    # Three DACL ACEs (AU, BA, SY) plus one SACL (WD).
    assert principals == ["AU", "BA", "SY", "WD"]


def test_htb_sacl_has_audit_type_and_failed_access_flag():
    anns = _parse(HTB_EXAMPLE)
    audit = _by_label(anns, "SYSTEM_AUDIT")
    failed = _by_label(anns, "FAILED_ACCESS")
    assert len(audit) == 1
    assert len(failed) == 1


def test_user_described_codes_resolve_correctly():
    """The exact mappings described in the project notes."""
    anns = _parse("D:(A;;CCLCSWRPLORC;;;AU)")
    by_code = {a.short_code: a.label for a in anns if a.category == "access_right"}
    assert by_code["CC"] == "SERVICE_QUERY_CONFIG"
    assert by_code["LC"] == "SERVICE_QUERY_STATUS"
    assert by_code["SW"] == "SERVICE_ENUMERATE_DEPENDENTS"
    assert by_code["RP"] == "SERVICE_START"
    assert by_code["LO"] == "SERVICE_INTERROGATE"
    assert by_code["RC"] == "READ_CONTROL"


def test_authenticated_users_sid():
    anns = _parse("D:(A;;CCLCSWRPLORC;;;AU)")
    principals = [a for a in anns if a.category == "principal"]
    assert principals[0].short_code == "AU"
    assert principals[0].label == "Authenticated Users"


def test_owner_section():
    anns = _parse("O:BAD:(A;;GA;;;SY)")
    sections = [a for a in anns if a.category == "section"]
    assert {a.short_code for a in sections} == {"O:", "D:"}


def test_no_sections_raises():
    try:
        _parse("not an sddl string")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_unclosed_ace_raises():
    try:
        _parse("D:(A;;GA;;;SY")
    except ValueError:
        return
    raise AssertionError("expected ValueError")
