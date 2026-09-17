# Jiminy Engine — GitHub Wiki

This page is a GitHub-wiki-oriented summary of the Jiminy Engine. For the full detailed
semantics see [`docs/JAIR_SEMANTICS.md`](docs/JAIR_SEMANTICS.md) and the worked examples in
[`docs/`](docs/).

Jiminy Engine is a Python implementation of the **Jiminy Advisor**, a normative reasoning
and argumentation framework for multi-stakeholder decision making:

> Liao, Pardo, Slavkovik & van der Torre (2023), *The Jiminy Advisor: Moral Agreements among
> Stakeholders Based on Norms and Argumentation*, JAIR.

---

## 1. What it does

Jiminy turns context facts and normative rules into **explainable moral recommendations**
combining normative systems, formal argumentation, stakeholder preferences and
context-dependent reasoning.

```
Context Facts
    -> YAML Scenario Loader
    -> Norm Representation  (body -> head, type, stakeholder)
    -> Argument Generation  (normative detachment)
    -> Argumentation Framework (arguments + attacks)
    -> Semantics Evaluation  (naive / grounded / preferred / stable / priority / jiminy)
    -> Accepted Arguments
    -> Moral Recommendations (deontic actions)
    -> Narrative Explanation
```

## 2. Scenario structure (YAML)

| Section | Purpose |
|---------|---------|
| `context` | brute facts `K` in `{id, description}` |
| `norms` | rules `(φ1..φn) ⇒^τ_s ψ` with `type` `c`/`r`/`p` and `stakeholder` |
| `contrariness` | opposition relation `χ` (`opposes` or `contraries`) |
| `priorities` | numeric urgency per conclusion (used by the `priority` semantics) |
| `base_priorities` | default authority per stakeholder |
| `meta_priorities` | context-dependent authority escalation `{if, stakeholder, value}` |

Norm types: `c` = constitutive (institutional fact), `r` = regulative (obligation),
`p` = permissive (permission).

## 3. Semantics

`compute_extension(arguments, semantics=...)`:

| Semantics | Definition |
|-----------|------------|
| `grounded` | skeptical least fixed point (Dung 1995) |
| `preferred` | maximal admissible set (Dung 1995) |
| `stable` | admissible set attacking everything outside (Dung 1995) |
| `naive` | maximal conflict-free set (ignores preferences) |
| `priority` | defeat by per-conclusion priority (Prakken & Sartor 1997) |
| `preferred_head` | preferred at the level of heads |

`compute_jiminy(context)` — classical two-phase **JAIR** semantics (Liao et al. 2023):

1. **Institutional closure** (least fixed point of constitutive rules),
2. **authority** from `base_priorities` + `meta_priorities`,
3. **permissions** and **obligations** via greedy selection by stakeholder authority.

Returns `(E, P, O)`; the recommendation is `P ∪ O`.

`compute_jiminy_bidirectional(context)` — same procedure but with a **bidirectional**
contrariety filter: it also drops an obligation whose head *attacks* an active element, so
every attack resolves to a single winner.

## 4. Getting started

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m cli.jiminy_cli --semantics jiminy scenarios/demo_COMMA2026_jair.yaml --facts w1 w2 w3 w4
```

From Python:

```python
from jiminy.engine import Jiminy
from jiminy.yaml_loader import load_scenario

(pf, norms, cont, prio, cd, nd, contrd, pd, bp, mp) = load_scenario("scenarios/demo_COMMA2026_jair.yaml")
jim = Jiminy(norms, cont, prio, cd, nd, contrd, pd, bp, mp)
E, P, O = jim.compute_jiminy(["w1", "w2", "w3", "w4"])
print(sorted(E), sorted(P), sorted(O))
```

## 5. Scenarios

- `agrobot.yaml`, `candy_unified.yaml`, `smoke_alarm.yaml`, `jiminy.yaml` — base examples.
- `jair.yaml`, `jair_base.yaml` — classical JAIR smart-speaker examples.
- `demo_COMMA2026_jair.yaml` — COMMA 2026 demo (same three stakeholders: Law, Household, Manuf).
- `jair_authority.yaml` — demonstrates that stakeholder authority decides a direct
  regulative-vs-regulative conflict.
- `turtlebot3_*.yaml` and `turtlebot3_*_jair.yaml` — TurtleBot3 obstacle avoidance and
  multi-robot cybersecurity (original scenario by Diego Pastrana, University of Leon).

## 6. Tests

```bash
source venv/bin/activate
python -m pytest
```

## 7. Repository layout

```
jiminy/         core engine (engine.py, norms.py, arguments.py, yaml_loader.py, visualization/)
cli/            command-line interface
scenarios/      YAML scenarios
notebooks/      Jupyter demonstrations (incl. turtlebot3_*.ipynb, demo_COMMA2026_jair.ipynb)
tests/          unit tests
docs/           documentation (JAIR_SEMANTICS.md, worked examples + figures)
```

## 8. Authors

- Francisco J. Rodríguez-Lera (University of León) — maintainer.
- Diego Pastrana (University of León) — original TurtleBot3 scenarios.
