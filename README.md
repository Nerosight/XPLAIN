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

Pull requests welcome for any of these:

- `--context file|registry|ad` for the sddl parser
- Full nmap parser: state explanations, `-sV` version detection, NSE script output
- Additional parsers: `wmic`, registry permission strings, `iptables -L`,
  `openssl x509 -text`, `ip route`, `dpkg -l` status codes
- `--json` output mode for tool-to-tool integration
- A `--no-banner` flag

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: a parser is a
single Python module that yields `Annotation` objects with character offsets.
The renderer and CLI handle everything else. See
[`docs/adding-a-parser.md`](docs/adding-a-parser.md) for a step-by-step.

## License

[MIT](LICENSE).
