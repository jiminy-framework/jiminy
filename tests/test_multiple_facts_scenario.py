# tests/test_candy_scenario.py

import subprocess


SCENARIO = "scenarios/candy_unified.yaml"


def run_jiminy(facts):

    cmd = [
        "python3",
        "-m",
        "cli.jiminy_cli",
        "--semantics",
        "priority",
        SCENARIO,
        "--facts",
        *facts
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout


# ----------------------------------------------------------------------
# BEFORE LUNCH
# ----------------------------------------------------------------------

def test_before_lunch():
    """
    BEFORE lunch → (w1, w3, w4, w5)
      → should activate: i_before → d1
    """

    out = run_jiminy(["w1", "w3", "w4", "w5"])

    assert "i_before accepted" in out
    assert "d1 accepted" in out

    # i_after should not activate
    assert "i_after accepted" not in out

    # Final recommendation must contain d1
    assert "Proposed actions:" in out
    assert "d1" in out


# ----------------------------------------------------------------------
# AFTER LUNCH
# ----------------------------------------------------------------------

def test_after_lunch():
    """
    AFTER lunch → (w1, w2, w4, w5)
      → should activate: i_after → p_no_intervene
    """

    out = run_jiminy(["w1", "w2", "w4", "w5"])

    assert "i_after accepted" in out
    assert "p_no_intervene accepted" in out

    # reminder should not activate
    assert "d1 accepted" not in out

    # Final recommendation must contain non-intervention
    assert "p_no_intervene" in out


# ----------------------------------------------------------------------
# SOFT MODE
# ----------------------------------------------------------------------

def test_soft_mode_activation():

    out = run_jiminy(["w1", "w3", "w4", "w5"])

    assert "i_soft accepted" in out
    assert "d4 accepted" in out


# ----------------------------------------------------------------------
# LEGAL RULE
# ----------------------------------------------------------------------

def test_legal_permission():

    out = run_jiminy(["w1", "w3", "w4", "w5"])

    assert "d5 accepted" in out