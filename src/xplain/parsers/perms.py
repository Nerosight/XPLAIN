"""Linux file permission strings: drwxr-xr-x, -rw-r--r--, etc.

Also accepts numeric mode like 4755 or 0755.
"""

from __future__ import annotations

import re
from typing import Iterable

from xplain.core.base import Annotation, Parser


# File type indicators (position 0 of the symbolic form).
_FILE_TYPES = {
    "-": ("Regular file", "An ordinary file."),
    "d": ("Directory", "A directory."),
    "l": ("Symbolic link", "A symbolic link to another path."),
    "c": ("Character device", "A character special device file (e.g. /dev/tty)."),
    "b": ("Block device", "A block special device file (e.g. /dev/sda)."),
    "p": ("Named pipe (FIFO)", "A named pipe used for IPC."),
    "s": ("Socket", "A Unix domain socket file."),
}

# Plain permission characters in each triplet.
_BASIC = {
    "r": ("read", "Permission to read."),
    "w": ("write", "Permission to write."),
    "x": ("execute", "Permission to execute (or traverse, for directories)."),
    "-": ("none", "No permission."),
}

# Special bits that can appear in the execute slot of a triplet.
# Key: (character, which-triplet).
_SPECIAL = {
    ("s", "owner"): (
        "setuid + execute",
        "Setuid bit set AND execute is granted. The process runs with the file owner's UID.",
    ),
    ("S", "owner"): (
        "setuid (no execute)",
        "Setuid bit set BUT execute is NOT granted. Usually a misconfiguration.",
    ),
    ("s", "group"): (
        "setgid + execute",
        "Setgid bit set AND execute is granted. The process runs with the file's group.",
    ),
    ("S", "group"): (
        "setgid (no execute)",
        "Setgid bit set BUT execute is NOT granted.",
    ),
    ("t", "other"): (
        "sticky + execute",
        "Sticky bit set AND execute is granted. On a directory, only the file's owner can rename/delete it.",
    ),
    ("T", "other"): (
        "sticky (no execute)",
        "Sticky bit set BUT execute is NOT granted.",
    ),
}

# Trailing indicators that some `ls` variants emit.
_TRAILING = {
    "+": ("Has ACL", "An extended ACL is attached to this file (see `getfacl`)."),
    ".": ("SELinux context", "An SELinux security context is attached."),
    "@": ("Extended attributes", "Extended attributes are present (common on macOS)."),
}

_TRIPLET_NAMES = ("owner", "group", "other")

_SYMBOLIC_RE = re.compile(r"^[-dlcbps][-rwsStT]{9}[+.@]?$")
_NUMERIC_RE = re.compile(r"^[0-7]{3,4}$")

class PermsParser(Parser):
    name = "perms"
    description = "Linux file permission strings (drwxr-xr-x) and numeric modes (4755)."
    example = "drwxr-xr-x"



    def detect(self, text: str) -> float:
        text = text.strip()
        if _SYMBOLIC_RE.match(text):
            return 0.9
        if _NUMERIC_RE.match(text):
            return 0.3
        return 0.0

    def parse(self, text: str) -> Iterable[Annotation]:
        text = text.strip()
        if text.isdigit() and 3 <= len(text) <= 4:
            yield from self._parse_numeric(text)
            return
        yield from self._parse_symbolic(text)

    # ------------------------------------------------------------------
    # symbolic mode: drwxr-xr-x
    # ------------------------------------------------------------------

    def _parse_symbolic(self, text: str) -> Iterable[Annotation]:
        if len(text) < 10:
            raise ValueError(
                f"expected at least 10 characters for symbolic mode, got {len(text)}"
            )

        # Position 0: file type.
        ftype = text[0]
        label, desc = _FILE_TYPES.get(
            ftype, ("Unknown type", f"Unrecognized file type {ftype!r}.")
        )
        yield Annotation(0, 1, label, ftype, desc, "file_type")

        # Positions 1-9: three triplets of (r, w, x|special).
        for triplet_index, who in enumerate(_TRIPLET_NAMES):
            base = 1 + triplet_index * 3
            yield from self._parse_triplet(text, base, who)

        # Optional trailing indicator (position 10).
        if len(text) >= 11:
            tail = text[10]
            if tail in _TRAILING:
                label, desc = _TRAILING[tail]
                yield Annotation(10, 11, label, tail, desc, "special_bit")

    def _parse_triplet(self, text: str, base: int, who: str) -> Iterable[Annotation]:
        # r slot
        ch = text[base]
        label, desc = _BASIC.get(ch, ("unknown", f"Unrecognized {ch!r}."))
        yield Annotation(
            base, base + 1, f"{who} {label}", ch, f"{who.capitalize()}: {desc}", "permission"
        )
        # w slot
        ch = text[base + 1]
        label, desc = _BASIC.get(ch, ("unknown", f"Unrecognized {ch!r}."))
        yield Annotation(
            base + 1, base + 2, f"{who} {label}", ch, f"{who.capitalize()}: {desc}", "permission"
        )
        # x slot - may be a special bit
        ch = text[base + 2]
        special_key = (ch, who)
        if special_key in _SPECIAL:
            label, desc = _SPECIAL[special_key]
            yield Annotation(base + 2, base + 3, label, ch, desc, "special_bit")
        else:
            label, desc = _BASIC.get(ch, ("unknown", f"Unrecognized {ch!r}."))
            yield Annotation(
                base + 2,
                base + 3,
                f"{who} {label}",
                ch,
                f"{who.capitalize()}: {desc}",
                "permission",
            )

    # ------------------------------------------------------------------
    # numeric mode: 4755 or 755
    # ------------------------------------------------------------------

    def _parse_numeric(self, text: str) -> Iterable[Annotation]:
        digits = text
        offset = 0
        if len(digits) == 4:
            yield from self._parse_special_digit(digits[0], 0)
            offset = 1
        for i, who in enumerate(_TRIPLET_NAMES):
            d = digits[offset + i]
            yield from self._parse_perm_digit(d, offset + i, who)

    def _parse_special_digit(self, d: str, pos: int) -> Iterable[Annotation]:
        n = int(d)
        bits = []
        if n & 4:
            bits.append("setuid")
        if n & 2:
            bits.append("setgid")
        if n & 1:
            bits.append("sticky")
        label = " + ".join(bits) if bits else "no special bits"
        desc = (
            "Special bits: "
            + (", ".join(bits) if bits else "none")
            + ". (4=setuid, 2=setgid, 1=sticky)"
        )
        yield Annotation(pos, pos + 1, label, d, desc, "special_bit")

    def _parse_perm_digit(self, d: str, pos: int, who: str) -> Iterable[Annotation]:
        n = int(d)
        bits = []
        if n & 4:
            bits.append("read")
        if n & 2:
            bits.append("write")
        if n & 1:
            bits.append("execute")
        label = f"{who}: {'+'.join(bits) if bits else 'none'}"
        desc = (
            f"{who.capitalize()} permissions: "
            + (", ".join(bits) if bits else "none")
            + ". (4=r, 2=w, 1=x)"
        )
        yield Annotation(pos, pos + 1, label, d, desc, "permission")
