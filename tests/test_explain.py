import pytest
from jiminy.norms import Norm
from jiminy.engine import Jiminy


def test_explain_hides_priorities_in_naive():
    norms = [
        Norm(["w1"], "d1", tau="p", stakeholder="X"),
    ]

    J = Jiminy(norms, contrariness={}, priorities={"d1": 10})

    accepted, rejected = J.compute_extension(["w1"], semantics="naive")

    text = J.explain(
        accepted,
        rejected,
        context=["w1"],
        generated_arguments=None,
        semantics="naive",
        debug=True,
    )

    assert "PRIORITY EVALUATION" not in text
    assert "priority=" not in text.lower()
