"""nmap default-output parser. STUB.

This is a placeholder so the registry has a third parser to demo. The next
iteration should:

  - Parse header lines like
      "Nmap scan report for scanme.nmap.org (45.33.32.156)"
      "Host is up (0.034s latency)."
      "Not shown: 996 closed tcp ports (reset)"
  - Parse the port table:
      PORT     STATE    SERVICE  VERSION
      22/tcp   open     ssh      OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13
      80/tcp   open     http     Apache httpd 2.4.7
  - Annotate each STATE token (open / closed / filtered / open|filtered /
    closed|filtered / unfiltered) with what it means and how nmap concluded it.
  - Explain the difference between a SERVICE column populated from
    nmap-services (port-number guess) versus -sV probes (real banner).

For now this parser only recognises the port-table header line so that
end-to-end CLI smoke tests work.
"""

from __future__ import annotations

import re
from typing import Iterable

from xplain.core.base import Annotation, Parser


_HEADER_RE = re.compile(r"^PORT\s+STATE\s+SERVICE(?:\s+VERSION)?", re.MULTILINE)

_STATES = {
    "open":            "An application is actively accepting connections on this port.",
    "closed":          "The port is reachable but no application is listening.",
    "filtered":        "Nmap could not determine state - likely a firewall blocking probes.",
    "unfiltered":      "Port is reachable but nmap cannot tell open vs closed (ACK scan).",
    "open|filtered":   "Nmap cannot tell open from filtered (UDP / IP protocol scans).",
    "closed|filtered": "Nmap cannot tell closed from filtered (idle scan).",
}

_PORT_LINE_RE = re.compile(
    r"^(?P<port>\d+/(?:tcp|udp|sctp))\s+(?P<state>\S+)\s+(?P<service>\S+)",
    re.MULTILINE,
)


class NmapParser(Parser):
    name = "nmap"
    description = "nmap default output (STUB - basic port-table only)."
    example = "PORT     STATE    SERVICE\n22/tcp   open     ssh"

    def parse(self, text: str) -> Iterable[Annotation]:
        for m in _HEADER_RE.finditer(text):
            yield Annotation(
                m.start(), m.end(),
                "Port table header", m.group(),
                "Column header for the port scan results.", "header",
            )

        for m in _PORT_LINE_RE.finditer(text):
            ps, pe = m.span("port")
            ss, se = m.span("state")
            svs, sve = m.span("service")
            port = m.group("port")
            state = m.group("state")
            service = m.group("service")

            yield Annotation(
                ps, pe, "Port/protocol", port,
                f"TCP/UDP port number and transport protocol.", "port",
            )
            state_desc = _STATES.get(
                state, f"Unrecognized state {state!r}."
            )
            yield Annotation(ss, se, f"State: {state}", state, state_desc, "state")
            yield Annotation(
                svs, sve, "Service guess", service,
                "Service name. Without -sV this is a guess from nmap-services "
                "by port number; with -sV it's based on a probe response.",
                "service",
            )
