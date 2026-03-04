import pytest
from jiminy.norms import Norm
from jiminy.engine import Jiminy


def test_conflict_detection():
    norms = [
        Norm(["w1"], "d1", tau="p", stakeholder="X"),
        Norm(["w1"], "d2", tau="p", stakeholder="X"),
    ]

    contrariness = {
        "d1": {"d2"},
    }

    J = Jiminy(norms, contrariness, priorities={})

    args = J.generate_arguments(["w1"])

    A = next(a for a in args if a.hd == "d1")
    B = next(a for a in args if a.hd == "d2")

    assert J.attacks(A, B) is True
    assert J.attacks(B, A) is False
