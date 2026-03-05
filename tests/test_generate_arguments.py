import pytest
from jiminy.norms import Norm
from jiminy.engine import Jiminy


def test_generate_arguments_with_closure():
    norms = [
        Norm(["w1"], "i1", tau="c", stakeholder="X"),
        Norm(["i1"], "d1", tau="p", stakeholder="X")
    ]

    J = Jiminy(norms, contrariness={}, priorities={}, context_desc={}, norm_desc={}, contrariness_desc={}, priority_desc={})

    args = J.generate_arguments(context=["w1"])

    # Should generate institutional i1 and permission d1
    heads = {A.hd for A in args}
    assert "i1" in heads
    assert "d1" in heads
