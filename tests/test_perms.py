"""Tests for the perms parser."""

from __future__ import annotations

from xplain.parsers.perms import PermsParser


def _by_offset(text):
    p = PermsParser()
    return {a.start: a for a in p.parse(text)}


def test_basic_directory():
    anns = _by_offset("drwxr-xr-x")
    assert anns[0].label == "Directory"
    assert anns[1].short_code == "r" and anns[1].label == "owner read"
    assert anns[2].label == "owner write"
    assert anns[3].label == "owner execute"
    assert anns[4].label == "group read"
    assert anns[5].label == "group none"
    assert anns[6].label == "group execute"


def test_setuid_with_execute():
    # Classic /usr/bin/passwd-style: -rwsr-xr-x
    anns = _by_offset("-rwsr-xr-x")
    assert anns[3].label == "setuid + execute"
    assert anns[3].category == "special_bit"


def test_setuid_without_execute():
    anns = _by_offset("-rwSr--r--")
    assert anns[3].label == "setuid (no execute)"


def test_sticky_on_other():
    # /tmp-style sticky directory: drwxrwxrwt
    anns = _by_offset("drwxrwxrwt")
    assert anns[9].label == "sticky + execute"
    assert anns[9].category == "special_bit"


def test_acl_indicator():
    anns = _by_offset("-rw-r--r--+")
    assert anns[10].label == "Has ACL"


def test_numeric_with_special_bits():
    p = PermsParser()
    anns = list(p.parse("4755"))
    # 4 = setuid, then 755 = rwx r-x r-x
    assert anns[0].short_code == "4"
    assert "setuid" in anns[0].label
    # Check owner = 7 -> read+write+execute
    assert "read" in anns[1].label and "write" in anns[1].label and "execute" in anns[1].label


def test_numeric_three_digits():
    p = PermsParser()
    anns = list(p.parse("755"))
    assert len(anns) == 3
    assert anns[0].short_code == "7"
    assert anns[1].short_code == "5"


def test_short_input_raises():
    p = PermsParser()
    try:
        list(p.parse("rwx"))
    except ValueError:
        return
    raise AssertionError("expected ValueError on too-short input")


def test_cli_accepts_dash_prefixed_input():
    """Regression: argparse should not eat input strings that start with '-'."""
    from xplain.cli import _preprocess_argv

    out = _preprocess_argv(["perms", "-rwsr-xr-x"])
    assert out == ["perms", "--", "-rwsr-xr-x"]

    # Regular inputs (no leading '-') should pass through unchanged.
    out = _preprocess_argv(["perms", "drwxr-xr-x"])
    assert out == ["perms", "drwxr-xr-x"]

    # Already-explicit '--' should also pass through unchanged.
    out = _preprocess_argv(["perms", "--", "-rwsr-xr-x"])
    assert out == ["perms", "--", "-rwsr-xr-x"]

    # Top-level flags before the subcommand are left alone.
    out = _preprocess_argv(["--list"])
    assert out == ["--list"]
