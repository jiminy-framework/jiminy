import yaml
import random

STAKEHOLDERS = [
    "Law",
    "Family",
    "Manufacturer",
    "Health",
    "School",
    "ChildProtection",
    "Insurance",
    "EthicsBoard",
    "Municipality",
    "RoboticsAuthority"
]


def random_stakeholder():
    return random.choice(STAKEHOLDERS)


def generate_scenario(
    n_constitutive=20,
    n_regulative=40,
    n_permissions=20
):

    norms = []
    contrariness = {}

    # ---------------------------------------------------
    # Generate constitutive chain
    # ---------------------------------------------------

    for i in range(1, n_constitutive):

        norms.append({
            "id": f"c{i}",
            "body": [f"i{i}"],
            "conclusion": f"i{i+1}",
            "type": "c",
            "stakeholder": random_stakeholder(),
            "description": "generated constitutive rule"
        })

    # ---------------------------------------------------
    # Generate obligations
    # ---------------------------------------------------

    for i in range(1, n_regulative):

        norms.append({
            "id": f"r{i}",
            "body": [f"i{random.randint(1, n_constitutive)}"],
            "conclusion": f"d{i}",
            "type": "r",
            "stakeholder": random_stakeholder(),
            "description": "generated obligation"
        })

    # ---------------------------------------------------
    # Generate permissions
    # ---------------------------------------------------

    start = n_regulative + 1

    for i in range(start, start + n_permissions):

        norms.append({
            "id": f"p{i}",
            "body": [f"i{random.randint(1, n_constitutive)}"],
            "conclusion": f"d{i}",
            "type": "p",
            "stakeholder": random_stakeholder(),
            "description": "generated permission"
        })

    # ---------------------------------------------------
    # Generate conflicts
    # ---------------------------------------------------

    total_actions = n_regulative + n_permissions

    for i in range(1, total_actions):

        opponents = random.sample(
            range(1, total_actions),
            k=random.randint(1, 3)
        )

        contrariness[f"d{i}"] = {
            "opposes": [f"d{x}" for x in opponents]
        }

    # ---------------------------------------------------
    # Scenario structure
    # ---------------------------------------------------

    scenario = {

        "semantics": "jiminy",

        "context": [
            {"id": "w1", "description": "child in room"},
            {"id": "w2", "description": "alcohol cabinet"},
            {"id": "w3", "description": "parent1 absent"},
            {"id": "w4", "description": "parent2 absent"}
        ],

        "norms": norms,

        "contrariness": contrariness,

        "priorities": {}
    }

    return scenario


if __name__ == "__main__":

    scenario = generate_scenario(
        n_constitutive=25,
        n_regulative=50,
        n_permissions=30
    )

    with open("benchmark_large.yaml", "w") as f:
        yaml.dump(scenario, f, sort_keys=False)

    print("Generated benchmark_large.yaml")
