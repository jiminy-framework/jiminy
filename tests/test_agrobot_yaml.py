import os
import pytest
from jiminy.yaml_loader import load_scenario
from jiminy.engine import Jiminy

# Path to the real YAML
SCENARIO_PATH = os.path.join(
    os.path.dirname(__file__),
    "../scenarios/agrobot.yaml"
)

# --------------------------------------------------------------------
# Helper to load the scenario
# --------------------------------------------------------------------
def load_agrobot():
    (
        context,
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_desc,
        contrariness_desc,
        priority_desc,
        base_priorities,
        meta_priorities,
    ) = load_scenario(SCENARIO_PATH)

    jim = Jiminy(
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_desc,
        contrariness_desc,
        priority_desc
    )

    return jim, context


# --------------------------------------------------------------------
# TEST 1 — the YAML loads without errors
# --------------------------------------------------------------------
def test_yaml_loads():
    jim, context = load_agrobot()
    assert isinstance(context, set)
    assert len(context) > 0
    assert len(jim.norms) > 0


# --------------------------------------------------------------------
# TEST 2 — arguments are generated
# --------------------------------------------------------------------
def test_argument_generation():
    jim, context = load_agrobot()

    args = jim.generate_arguments(context)
    assert len(args) > 0, "El motor debe generar argumentos desde el YAML."

    # There must be at least constitutive (i_) and deontic (d_)
    heads = [a.hd for a in args]
    assert any(h.startswith("i") for h in heads)
    assert any(h.startswith("d") for h in heads)


# --------------------------------------------------------------------
# TEST 3 — conflict between gate closing and safety override (if they exist)
# --------------------------------------------------------------------
def test_conflict_detection_if_applicable():
    jim, context = load_agrobot()
    args = jim.generate_arguments(context)

    contr = jim.contrariness

    # If the YAML defines these symbols, they must be contrary
    if "d_close_gate" in contr:
        assert "d_do_not_act" in contr["d_close_gate"], \
            "El YAML debe marcar d_close_gate ↔ d_do_not_act como contrarios"

    # Don't fail if the YAML defines other symbols
    assert isinstance(contr, dict)


# --------------------------------------------------------------------
# TEST 4 — priority: the engine must select a non-empty set
# --------------------------------------------------------------------
def test_prioritized_extension_produces_decision():
    jim, context = load_agrobot()

    args = jim.generate_arguments(context)
    accepted, rejected = jim.compute_extension(args)

    assert len(accepted) > 0

    # There must be at least one d* among the actions
    assert any(a.hd.startswith("d") for a in accepted)


# --------------------------------------------------------------
