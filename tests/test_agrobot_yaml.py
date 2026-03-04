import os
import pytest
from jiminy.yaml_loader import load_scenario
from jiminy.engine import Jiminy

# Ruta al YAML real
SCENARIO_PATH = os.path.join(
    os.path.dirname(__file__),
    "../scenarios/agrobot.yaml"
)

# --------------------------------------------------------------------
# Helper para cargar el escenario
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
# TEST 1 — el YAML se carga sin errores
# --------------------------------------------------------------------
def test_yaml_loads():
    jim, context = load_agrobot()
    assert isinstance(context, set)
    assert len(context) > 0
    assert len(jim.norms) > 0


# --------------------------------------------------------------------
# TEST 2 — se generan argumentos
# --------------------------------------------------------------------
def test_argument_generation():
    jim, context = load_agrobot()

    args = jim.generate_arguments(context)
    assert len(args) > 0, "El motor debe generar argumentos desde el YAML."

    # Al menos debe haber constitutivos (i_) y deónticos (d_)
    heads = [a.hd for a in args]
    assert any(h.startswith("i") for h in heads)
    assert any(h.startswith("d") for h in heads)


# --------------------------------------------------------------------
# TEST 3 — conflicto entre gate closing y safety override (si existen)
# --------------------------------------------------------------------
def test_conflict_detection_if_applicable():
    jim, context = load_agrobot()
    args = jim.generate_arguments(context)

    contr = jim.contrariness

    # Si el YAML define estos símbolos, deben ser contrarios
    if "d_close_gate" in contr:
        assert "d_do_not_act" in contr["d_close_gate"], \
            "El YAML debe marcar d_close_gate ↔ d_do_not_act como contrarios"

    # No fallar si el YAML define otros símbolos
    assert isinstance(contr, dict)


# --------------------------------------------------------------------
# TEST 4 — prioridad: el motor debe seleccionar un conjunto no vacío
# --------------------------------------------------------------------
def test_prioritized_extension_produces_decision():
    jim, context = load_agrobot()

    args = jim.generate_arguments(context)
    accepted, rejected = jim.compute_extension(args)

    assert len(accepted) > 0

    # Debe haber al menos un d* en las acciones
    assert any(a.hd.startswith("d") for a in accepted)


# --------------------------------------------------------------
