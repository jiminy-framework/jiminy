import yaml
from collections import defaultdict


def validate_scenario(path):

    print(f"\nValidating scenario: {path}\n")

    with open(path) as f:
        data = yaml.safe_load(f)

    norms = data.get("norms", [])
    contrariness = data.get("contrariness", {})
    meta = data.get("meta_priorities", [])

    errors = []
    warnings = []

    conclusions = set()
    bodies = set()
    stakeholders = set()

    # -------------------------------------------------
    # scan norms
    # -------------------------------------------------

    for n in norms:

        nid = n["id"]

        if "conclusion" not in n:
            errors.append(f"{nid} has no conclusion")

        if "body" not in n:
            errors.append(f"{nid} has no body")

        conclusions.add(n["conclusion"])
        bodies.update(n["body"])

        stakeholders.add(n["stakeholder"])

    # -------------------------------------------------
    # orphan institutional facts
    # -------------------------------------------------

    institutional = {c for c in conclusions if c.startswith("i")}

    for i in institutional:
        if i not in bodies:
            warnings.append(f"institutional fact {i} is never used in any rule")

    # -------------------------------------------------
    # orphan decisions
    # -------------------------------------------------

    decisions = {c for c in conclusions if c.startswith("d")}

    for d in decisions:
        if d not in contrariness:
            warnings.append(f"decision {d} has no contrariness entry")

    # -------------------------------------------------
    # check contrariness references
    # -------------------------------------------------

    for d, entry in contrariness.items():

        for opp in entry.get("opposes", []):

            if opp not in decisions:
                warnings.append(
                    f"{d} opposes {opp} but {opp} is not a decision"
                )

    # -------------------------------------------------
    # detect duplicate stakeholders
    # -------------------------------------------------

    normalized = defaultdict(list)

    for s in stakeholders:
        normalized[s.lower()].append(s)

    for key, vals in normalized.items():
        if len(vals) > 1:
            warnings.append(
                f"possible duplicate stakeholders: {vals}"
            )

    # -------------------------------------------------
    # meta priority validation
    # -------------------------------------------------

    for m in meta:

        trigger = m["if"]
        stakeholder = m["stakeholder"]

        if trigger not in conclusions:
            warnings.append(
                f"meta-priority trigger {trigger} is never produced"
            )

        if stakeholder not in stakeholders:
            warnings.append(
                f"meta-priority references unknown stakeholder {stakeholder}"
            )

    # -------------------------------------------------
    # results
    # -------------------------------------------------

    if errors:
        print("ERRORS")
        print("------")
        for e in errors:
            print("•", e)

    if warnings:
        print("\nWARNINGS")
        print("--------")
        for w in warnings:
            print("•", w)

    if not errors and not warnings:
        print("Scenario OK ✓")

    print("\nSummary")
    print("-------")
    print("norms:", len(norms))
    print("stakeholders:", len(stakeholders))
    print("institutional facts:", len(institutional))
    print("decisions:", len(decisions))
    print("conflict nodes:", len(contrariness))


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print("Usage: python validate_scenario.py scenario.yaml")
        exit(1)

    validate_scenario(sys.argv[1])