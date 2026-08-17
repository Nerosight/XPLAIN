# xplain

> Annotate and explain cryptic command output. One CLI for the security/sysadmin references that are scattered across a dozen sites.

<!-- Add a screenshot here once you have one. Suggested:
     run `xplain sddl 'D:(A;;CCLCSWRPLORC;;;AU)'` in your terminal,
     screenshot the colored output, save as docs/screenshot.png -->
<!-- ![xplain decoding an SDDL string](docs/screenshot.png) -->

## Why

When you see something like:

```
D:(A;;CCLCSWRPLORC;;;AU)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)
```

...explainshell can't help. Microsoft's docs make you click through five pages.
`xplain` decodes the whole string in one place: which section, which ACE type,
which access rights, which security principal.

## Install

```bash
pipx install xplain
```

Or from a clone:

```bash
git clone https://github.com/Nerosight/xplain
cd xplain
pip install -e ".[dev]"
```

## Usage

```bash
# Linux file permissions
xplain perms drwxr-xr-x
xplain perms -rwsr-xr-x          # leading-dash inputs are handled
xplain perms 4755                 # numeric mode also works

# Windows SDDL strings (e.g. from `sc sdshow <service>`)
xplain sddl "D:(A;;CCLCSWRPLORC;;;AU)"

# nmap output (pipe directly)
nmap -sV scanme.nmap.org | xplain nmap

# List all available parsers
xplain --list
```

## Available parsers

| Parser   | Status   | Example                                              |
|----------|----------|------------------------------------------------------|
| `perms`  | stable   | `xplain perms drwxr-xr-x`                            |
| `sddl`   | stable*  | `xplain sddl "D:(A;;CCLCSWRPLORC;;;AU)"`             |
| `nmap`   | stub     | `nmap -sV target \| xplain nmap`                     |

\* `sddl` currently uses **service-object** context for the rights field. The
same two-letter codes mean different things on files, registry keys, and AD
objects - `--context` is on the roadmap.
## Roadmap

Adding a format is deliberately a contained piece of work: a parser is one
module that yields annotated spans, and the CLI and renderer pick it up
automatically. The items below are grouped by what each one asks of that
architecture.

### In progress — format auto-detection

Today you have to know what a format is called before `xplain` can help you,
which is backwards: not knowing is usually the reason you're here. Detection
lets each parser score how confident it is that a given input is its format, so
`xplain "D:(A;;CCLCSWRPLORC;;;AU)"` routes itself, and genuinely ambiguous
input returns a ranked list of candidates rather than a guess.

- [x] `detect()` on the parser base class, defaulting to "not mine"
- [ ] `detect()` implementations for `perms`, `sddl`, `nmap`
- [ ] `registry.detect_all()` — poll every parser, rank by confidence
- [ ] CLI dispatch for input given without a subcommand

### Accuracy

- `--context file|registry|ad` for `sddl`. The rights field currently assumes
  service-object context; the same two-letter codes mean different things on
  files, registry keys, and AD objects. This is the known correctness gap.
- Full `nmap` parser: state explanations, `-sV` version detection, and NSE
  script output. The current parser reads the port table only.

### Coverage

New parsers, roughly ordered by how often each one turns up in a support queue:

- `iptables -L` rule listings
- `ip route` output
- Windows registry permission strings
- `openssl x509 -text` certificate fields
- `dpkg -l` status codes
- `wmic` output

### Integration

- `--json` output mode, so annotations can feed other tools
- `--no-banner`, for clean piping

Pull requests are welcome for any of these. The Coverage items are the most
self-contained if you're starting out — see
[`docs/adding-a-parser.md`](docs/adding-a-parser.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: a parser is a
single Python module that yields `Annotation` objects with character offsets.
The renderer and CLI handle everything else. See
[`docs/adding-a-parser.md`](docs/adding-a-parser.md) for a step-by-step.

## License

[MIT](LICENSE).
