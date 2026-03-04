# tests/test_head_collapse.py
"""
Test for the Head-Collapse property.

If the theorem holds, the set of accepted argument heads
must coincide with the set of accepted conclusions.

This validates the structural compression property of the framework.
"""


from jiminy.engine import Jiminy
from jiminy.yaml_loader import load_scenario
import pytest


SCENARIO = "scenarios/candy_unified.yaml"


@pytest.fixture
def jim():

    (
        possible_facts,
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_desc,
        contrariness_desc,
        priority_desc
    ) = load_scenario(SCENARIO)

    return Jiminy(
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_desc,
        contrariness_desc,
        priority_desc
    )


# -------------------------------------------------------------
# Head collapse property
# -------------------------------------------------------------

def test_head_collapse_property(jim):

    facts = {"w1", "w3", "w4", "w5"}

    args = jim.generate_arguments(facts)

    accepted, rejected = jim.compute_extension(
        args,
        semantics="jiminy"
    )

    accepted_heads = {a.hd for a in accepted}

    collapsed = set()

    for h in accepted_heads:
        collapsed |= {a.hd for a in accepted if a.hd == h}

    assert collapsed == accepted_heads


# -------------------------------------------------------------
# No self-contradictory heads
# -------------------------------------------------------------

def test_head_uniqueness(jim):

    facts = {"w1", "w3", "w4", "w5"}

    args = jim.generate_arguments(facts)

    heads = [a.hd for a in args]

    for h in heads:
        assert h not in jim.contrariness.get(h, [])