"""Property tests for Detection: invariants that must hold for any input.

Valid samples are built from each parser's own lookup tables. Near-misses are
valid samples with a few characters dropped, inserted or replaced, or cut
down to a prefix or suffix, which is where detect() and parse() are most
likely to disagree.
"""

from __future__ import annotations

from hypothesis import example, given
from hypothesis import strategies as st

from xplain.detection import Chosen, resolve
from xplain.parsers import perms, sddl


# ---------------------------------------------------------------------------
# valid samples
# ---------------------------------------------------------------------------

def _triplet(who: str):
    specials = [ch for (ch, w) in perms._SPECIAL if w == who]
    return st.tuples(
        st.sampled_from("r-"), st.sampled_from("w-"), st.sampled_from(["x", "-"] + specials)
    ).map("".join)


perms_symbolic = st.tuples(
    st.sampled_from(sorted(perms._FILE_TYPES)),
    _triplet("owner"),
    _triplet("group"),
    _triplet("other"),
    st.sampled_from([""] + sorted(perms._TRAILING)),
).map("".join)

perms_numeric = st.text(alphabet="01234567", min_size=3, max_size=4)

_two_letter = lambda table: st.lists(st.sampled_from(sorted(table)), max_size=4).map("".join)

_sid = st.one_of(
    st.sampled_from(sorted(sddl._WELL_KNOWN_SIDS)),
    st.lists(st.integers(0, 4294967295), min_size=1, max_size=5).map(
        lambda parts: "S-1-5-" + "-".join(map(str, parts))
    ),
)

_ace = st.builds(
    lambda t, f, r, s: f"({t};{f};{r};;;{s})",
    st.sampled_from(sorted(sddl._ACE_TYPES)),
    _two_letter(sddl._ACE_FLAGS),
    st.lists(st.sampled_from(sorted(sddl._SERVICE_RIGHTS)), min_size=1, max_size=6).map("".join),
    _sid,
)

sddl_string = st.builds(
    lambda owner, group, kind, flags, aces: owner + group + kind + flags + "".join(aces),
    st.one_of(st.just(""), _sid.map(lambda s: "O:" + s)),
    st.one_of(st.just(""), _sid.map(lambda s: "G:" + s)),
    st.sampled_from(["D:", "S:"]),
    st.sampled_from(["", "P", "AI", "PAI", "AR"]),
    st.lists(_ace, min_size=1, max_size=4),
)

nmap_port_lines = st.lists(
    st.builds(
        lambda port, proto, state, service: f"{port}/{proto}   {state}   {service}",
        st.integers(1, 65535),
        st.sampled_from(["tcp", "udp", "sctp"]),
        st.sampled_from(["open", "closed", "filtered", "unfiltered", "open|filtered"]),
        st.sampled_from(["ssh", "http", "https", "domain", "msrpc", "unknown"]),
    ),
    min_size=1,
    max_size=5,
).map("\n".join)

_valid = {"perms": st.one_of(perms_symbolic, perms_numeric), "sddl": sddl_string, "nmap": nmap_port_lines}


# ---------------------------------------------------------------------------
# near-misses
# ---------------------------------------------------------------------------

_NOISE = "-rwxsStT0123456789OGDS:();AU \n\\"


@st.composite
def near_miss(draw):
    text = draw(st.one_of(*_valid.values()))
    for _ in range(draw(st.integers(1, 3))):
        # Half the time, cut where a person would: at a bracket, colon, separator or line.
        boundaries = [j for j, c in enumerate(text) if c in "():; \n"]
        if boundaries and draw(st.booleans()):
            i = draw(st.sampled_from(boundaries))
        else:
            i = draw(st.integers(0, len(text)))
        edit = draw(st.sampled_from(["drop", "insert", "replace", "keep-prefix", "keep-suffix"]))
        ch = draw(st.sampled_from(_NOISE))
        if edit == "drop":
            text = text[:i] + text[i + 1 :]
        elif edit == "insert":
            text = text[:i] + ch + text[i:]
        elif edit == "replace":
            text = text[:i] + ch + text[i + 1 :]
        elif edit == "keep-prefix":
            text = text[:i]
        else:  # a partial copy-paste from the middle onwards
            text = text[i:]
    return text


# Near-misses are where bugs live, so they get half the weight.
any_input = st.one_of(st.text(), *_valid.values(), near_miss(), near_miss(), near_miss(), near_miss())


# ---------------------------------------------------------------------------
# properties
# ---------------------------------------------------------------------------

@given(any_input)
@example("G:S-1-5-1000-1000-940S:(AU;;CRCCCRCCCCSD;;;WD)(A;;CC;;;AN")  # truncated mid-ACE
def test_a_chosen_parser_can_parse_the_input(text):
    outcome = resolve(text)
    if isinstance(outcome, Chosen):
        list(outcome.parser.parse(text.strip()))


@given(any_input)
def test_resolve_never_raises_and_is_deterministic(text):
    assert resolve(text) == resolve(text)


@given(st.sampled_from(sorted(_valid)).flatmap(lambda name: st.tuples(st.just(name), _valid[name])))
def test_valid_samples_are_chosen_as_their_parser(case):
    name, text = case
    outcome = resolve(text)
    assert isinstance(outcome, Chosen), outcome
    assert outcome.parser.name == name
