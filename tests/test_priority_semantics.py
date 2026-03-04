import pytest
from jiminy.norms import Norm
from jiminy.engine import Jiminy


def test_priority_semantics_selects_highest_priority():
    norms = [
        Norm(["w1"], "d1", tau="p", stakeholder="X"),
        Norm(["w1"], "d2", tau="p", stakeholder="X"),
    ]

    contrariness = {
        "d1": {"d2"},
        "d2": {"d1"},
    }

    priorities = {
        "d1": 1,
        "d2": 5,   # highest priority
    }

    J = Jiminy(norms, contrariness, priorities)
    args = J.generate_arguments(["w1"])
    accepted, rejected = J.compute_extension(args, semantics="priority")

    heads = {A.hd for A in accepted}
    assert heads == {"d2"}
