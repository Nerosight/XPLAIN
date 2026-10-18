# xplain

xplain annotates cryptic command output (permission strings, SDDL, nmap) so a person can read it. This glossary fixes the words used for its parts.

## Language

### Core

**Format**:
A well-defined kind of cryptic text that xplain can explain, such as a Linux permission string or an SDDL string.
_Avoid_: type, kind, language

**Parser**:
The code that knows one Format: it recognises it and explains its parts.
_Avoid_: handler, decoder, plugin

**Annotation**:
One explained span of the input: where it sits, what it is called, and what it means.
_Avoid_: token, highlight, tag

### Detection

**Detection**:
Working out which Format an input is in when the user did not name one.
_Avoid_: auto-detect, sniffing, routing

**Confidence**:
A Parser's score from 0.0 to 1.0 for how sure it is that an input is in its Format.
_Avoid_: probability, likelihood, weight

**Candidate**:
A Parser that gave an input a Confidence above zero, ranked against the others.
_Avoid_: guess, match, suggestion

**Chosen**:
The Detection outcome where one Candidate is clearly the input's Format.
_Avoid_: match, winner, detected

**Ambiguous**:
The Detection outcome where Candidates exist but none is clear enough to pick.
_Avoid_: unsure, tie, conflict

**Unknown**:
The Detection outcome where no Parser recognised the input at all.
_Avoid_: unrecognised, no match, failed
