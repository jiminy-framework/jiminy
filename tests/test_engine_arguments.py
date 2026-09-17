from jiminy.engine import Jiminy
from jiminy.norms import Norm

def test_argument_closure():
    norms = [
        Norm(("w1",), "i1", "c", "H"),
        Norm(("i1",), "d1", "r", "H")
    ]

    context = {"w1"}

    jim = Jiminy(norms, {}, {}, {}, {}, {}, {})
    args = jim.generate_arguments(context)

    # Institutional fact i1 must appear
    assert any(a.hd == "i1" for a in args)

    # Action d1 must also be generated because i1 is added by closure
    assert any(a.hd == "d1" for a in args)


def test_priority_defeat():
    norms = [
        Norm(("w1",), "d1", "r", "H"),
        Norm(("w1",), "d2", "r", "H")
    ]
    contrariness = {"d1": {"d2"}, "d2": {"d1"}}
    priorities = {"d1": 5, "d2": 1}

    jim = Jiminy(norms, contrariness, priorities, {}, {}, {}, {})
    context = {"w1"}

    args = jim.generate_arguments(context)
    accepted, rejected = jim.compute_extension(args)

    # Only d1 must survive
    assert any(a.hd == "d1" for a in accepted)
    assert not any(a.hd == "d2" for a in accepted)
    assert any(a.hd == "d2" for a in rejected)
