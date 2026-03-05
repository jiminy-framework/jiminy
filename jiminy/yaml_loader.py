import yaml
from .norms import Norm


def load_scenario(path):

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # ================================================================
    # CONTEXT  → BRUTE FACTS (K)
    # ================================================================

    possible_facts = {item["id"] for item in data["context"]}

    context_desc = {
        item["id"]: item.get("description", item.get("desc", ""))
        for item in data["context"]
    }

    # ================================================================
    # RULES → collect from different YAML sections
    # ================================================================

    norms = []
    norm_descriptions = {}

    all_rules = []

    # old format
    if "norms" in data:
        all_rules.extend(data["norms"])

    # new formats
    if "constitutive_norms" in data:
        for r in data["constitutive_norms"]:
            rule = r.copy()
            rule["type"] = "c"
            all_rules.append(rule)

    if "regulative_norms" in data:
        for r in data["regulative_norms"]:
            rule = r.copy()
            rule["type"] = "r"
            all_rules.append(rule)

    if "permissions" in data:
        for r in data["permissions"]:
            rule = r.copy()
            rule["type"] = "p"
            all_rules.append(rule)

    # build Norm objects
    for r in all_rules:

        norms.append(
            Norm(
                tuple(r["body"]),
                r["conclusion"],
                r["type"],
                r["stakeholder"],
                norm_id=r["id"]
            )
        )

        norm_descriptions[r["conclusion"]] = r.get(
            "description", r.get("desc", "")
        )

    # ================================================================
    # CONTRARIETIES
    # ================================================================

    contrariness = {}
    contrariness_desc = {}

    for concl, block in data.get("contrariness", {}).items():

        contrariness[concl] = set(
            block.get("opposes", block.get("contraries", []))
        )

        contrariness_desc[concl] = block.get("description", "")

    # ================================================================
    # PRIORITIES
    # ================================================================

    priorities = {}
    priority_desc = {}

    for concl, pdata in data.get("priorities", {}).items():

        priorities[concl] = pdata.get("value", 0)

        priority_desc[concl] = pdata.get("description", "")

    # ================================================================
    # BASE PRIORITIES (stakeholder authority)
    # ================================================================

    base_priorities = data.get("base_priorities", {})
    print(f"[INFO] Base priorities loaded: {len(base_priorities)}")

    # ================================================================
    # META PRIORITIES (dynamic authority rules)
    # ================================================================

    meta_priorities = data.get("meta_priorities", [])
    print(f"[INFO] Meta-priority rules loaded: {len(meta_priorities)}")
    
    # ================================================================
    # RETURN STRUCTURE
    # ================================================================

    return (
        possible_facts,
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_descriptions,
        contrariness_desc,
        priority_desc,
        base_priorities,
        meta_priorities
    )