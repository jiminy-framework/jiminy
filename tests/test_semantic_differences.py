# tests/test_semantic_differences.py
"""
Test that different semantics produce different recommendations.

This validates that the framework behaviour depends on the chosen
argumentation semantics.
"""

import subprocess
import logging
import os

# logging.basicConfig(
#     level=logging.DEBUG if os.getenv("JIMINY_DEBUG") else logging.INFO
# )


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCENARIO = "scenarios/candy_unified.yaml"


def run_semantics(semantics, facts):

    cmd = [
        "python3",
        "-m",
        "cli.jiminy_cli",
        "--semantics",
        semantics,
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


def extract_actions(output):
    """
    Extract the 'Proposed actions' line.
    """

    for line in output.splitlines():
        if "Proposed actions:" in line:
            return line.strip()

    return ""



def test_semantics_produce_different_results():
    """
    Verify that naive, priority and jiminy semantics
    can produce different recommendations.
    """
    facts = ["w1", "w3", "w4", "w5"]

    logger.info("Testing semantic differences with facts: %s", facts)

    naive_out = run_semantics("naive", facts)
    priority_out = run_semantics("priority", facts)
    jiminy_out = run_semantics("jiminy", facts)

    naive_actions = extract_actions(naive_out)
    priority_actions = extract_actions(priority_out)
    jiminy_actions = extract_actions(jiminy_out)

    logger.info("Naive output:\n%s", naive_out)
    logger.info("Priority output:\n%s", priority_out)
    logger.info("Jiminy output:\n%s", jiminy_out)

    logger.info("Extracted actions:")
    logger.info("Naive   : %s", naive_actions)
    logger.info("Priority: %s", priority_actions)
    logger.info("Jiminy  : %s", jiminy_actions)

    # Ensure outputs exist
    assert naive_actions != "", "Naive semantics produced no actions"
    assert priority_actions != "", "Priority semantics produced no actions"
    assert jiminy_actions != "", "Jiminy semantics produced no actions"

    # At least one semantics must differ
    unique_results = {
        naive_actions,
        priority_actions,
        jiminy_actions
    }

    logger.debug("Unique semantic results: %s", unique_results)

    assert len(unique_results) > 1, (
        "All semantics produced identical recommendations:\n"
        f"Naive   : {naive_actions}\n"
        f"Priority: {priority_actions}\n"
        f"Jiminy  : {jiminy_actions}"
    )

def test_semantics_are_deterministic():

    facts = ["w1", "w3", "w4", "w5"]

    out1 = run_semantics("priority", facts)
    out2 = run_semantics("priority", facts)

    assert extract_actions(out1) == extract_actions(out2)