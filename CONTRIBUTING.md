# Contributing to xplain

Thanks for considering a contribution.

## What's wanted

The two highest-impact areas:

**New parsers.** Anything that produces cryptic, well-defined output is fair
game. Active wishlist:

- Windows `icacls` output (file/registry SDDL with file context)
- `wmic` output
- `iptables -L` rules
- `openssl x509 -text` certificate dumps
- `ip route` / `ip a`
- `dpkg -l` status codes (`ii`, `rc`, etc.)
- nmap `-sV` and NSE script output

**Filling out existing parsers.** The `sddl` parser only covers
service-object context today. File, registry, and AD-object contexts use the
same two-letter codes for different rights - adding a `--context` flag with
the alternate lookup tables would be a huge win.

## How to add a parser

See [`docs/adding-a-parser.md`](docs/adding-a-parser.md). The contract is
tiny: subclass `Parser`, yield `Annotation` objects pointing at character
spans, register in `xplain/registry.py`.

## Setup

```bash
git clone https://github.com/Nerosight/xplain
cd xplain
pip install -e ".[dev]"
pytest
```

## Style

- Lookup tables over branching. The whole project is data-driven by design.
- Deterministic, offline. No LLM calls, no network access, no calling out
  to external tools.
- Tests required for any new parser. Cover at least the happy path plus
  one regression case.
- Match the existing code style (PEP 8, type hints, docstrings on public
  functions).

## Submitting a PR

- Branch from `main`.
- Make focused commits with clear messages.
- Add or update tests.
- Update `CHANGELOG.md` under an "Unreleased" section.
- Make sure CI is green before requesting review.

## Filing issues

Use the issue templates. For bugs, include the exact input and the expected
vs actual output. For new parser requests, include a real-world example of
the format you want decoded.
