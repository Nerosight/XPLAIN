"""End-to-end tests for the CLI's handling of Detection outcomes."""

from __future__ import annotations

from xplain.cli import main


def test_numeric_mode_is_detected_as_perms(capsys):
    code = main(["755"])
    out, err = capsys.readouterr()
    assert code == 0
    assert "owner: read+write+execute" in out
    assert "Detected: Linux file permission strings" in err


def test_single_ambiguous_candidate_suggests_that_parser(capsys):
    code = main(["(A;;GA;;;SY)"])
    _, err = capsys.readouterr()
    assert code == 4
    assert "error: not sure this is sddl. try: xplain sddl '(A;;GA;;;SY)'" in err
    assert "ambiguous" not in err


def test_unknown_input_lists_every_parser(capsys):
    code = main(["hello world"])
    _, err = capsys.readouterr()
    assert code == 4
    assert "error: could not identify this format." in err
    for name in ("nmap", "perms", "sddl"):
        assert f"xplain {name}" in err
