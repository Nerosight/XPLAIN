# Changelog

All notable changes to this project will be documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Initial release

### Added
- `perms` parser: Linux file permission strings (`drwxr-xr-x`) and numeric
  modes (`4755`). Handles special bits (setuid/setgid/sticky) and trailing
  ACL/SELinux indicators.
- `sddl` parser (service-object context): O/G/D/S sections, ACL flags, all
  documented ACE types and flags, full standard + service rights, ~45
  well-known SIDs.
- `nmap` parser stub: recognises the port-table header and basic port lines.
- Colored CLI rendering via `rich`, plus a legend table mapping every token
  to its name and meaning.
- Stdin support: `nmap -sV target | xplain nmap`.
- Auto-handling of leading-dash inputs (`xplain perms -rwsr-xr-x`).
- ASCII banner on `xplain` and `xplain --list`, suppressed on non-TTY.
- 21 tests covering both parsers and CLI edge cases.
