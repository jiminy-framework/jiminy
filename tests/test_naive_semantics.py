import pytest
from jiminy.norms import Norm
from jiminy.engine import Jiminy


def test_naive_does_not_use_priority():
    norms = [
        Norm(["w1"], "d1", tau="p", stakeholder="X"),
        Norm(["w1"], "d2", tau="p", stakeholder="X"),
    ]

    contrariness = {
        "d1": {"d2"},
        "d2": {"d1"},
    }

    # d1 is lower priority but naive should ignore this
    priorities = {
        "d1": 1,
        "d2": 99,
    }

    J = Jiminy(norms, contrariness, priorities)

    accepted, rejected = J.compute_extension(["w1"], semantics="naive")

    # Greedy selection: d1 appears before d2 → choose d1 only
    heads = {A.hd for A in accepted}
    assert heads == {"d1"}
