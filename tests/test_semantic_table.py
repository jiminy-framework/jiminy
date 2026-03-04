import os
import glob
import subprocess
import yaml

SCENARIO_DIR = "scenarios"


def run_semantics(semantics, facts, scenario):

    cmd = [
        "python3",
        "-m",
        "cli.jiminy_cli",
        "--semantics",
        semantics,
        scenario,
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
    Extract actions from 'Proposed actions:' line.
    """

    for line in output.splitlines():

        if "Proposed actions:" in line:

            return line.split(":", 1)[1].strip()

    return ""

def load_all_facts(scenario_path):
    """
    Extract all context fact IDs from the YAML scenario.
    """
    with open(scenario_path, "r") as f:
        data = yaml.safe_load(f)

    return [f["id"] for f in data.get("context", [])]


def test_semantic_comparison_table():

    scenarios = sorted(glob.glob(os.path.join(SCENARIO_DIR, "*.yaml")))

    print("\n\nSEMANTIC COMPARISON TABLE\n")

    header = f"| {'Scenario':18} | {'Naive':35} | {'Priority':35} | {'Jiminy':35} |"
    sep = "|" + "-" * (len(header) - 2) + "|"

    print(header)
    print(sep)

    for s in scenarios:

        facts = load_all_facts(s)

        naive = extract_actions(run_semantics("naive", facts, s)) or "∅"
        priority = extract_actions(run_semantics("priority", facts, s)) or "∅"
        jiminy = extract_actions(run_semantics("jiminy", facts, s)) or "∅"

        name = os.path.basename(s)

        print(
            f"| {name:18} | {naive:35} | {priority:35} | {jiminy:35} |"
        )

    print(sep)