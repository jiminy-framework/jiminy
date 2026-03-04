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

    # Hecho institucional i1 debe aparecer
    assert any(a.hd == "i1" for a in args)

    # Acción d1 también debe generarse porque i1 se añade por clausura
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

    # Solo d1 debe sobrevivir
    assert any(a.hd == "d1" for a in accepted)
    assert not any(a.hd == "d2" for a in accepted)
    assert any(a.hd == "d2" for a in rejected)
