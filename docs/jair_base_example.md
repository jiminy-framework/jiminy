# `jair_base.yaml` — Fine-grained, step-by-step walkthrough

## 0. Formalization of Jiminy and its semantics

### 0.1 The normative system

A **Jiminy normative system** is a tuple

```
NS = ( K, R, χ, ≻ )
```

where:

- `K` — set of **brute facts** (the context) `K ⊆ Facts`,
- `R` — set of **norms** (rules),
- `χ : Conclusions → 2^Conclusions` — the **contrariety** function,
- `≻ ⊆ Conclusions × Conclusions` — a **preference ordering** over conclusions
  (in the priority semantics) or, in the classic JAIR semantics, an ordering derived
  from **stakeholder authority**.

### 0.2 Norms

A norm is a labeled rule of the form

```
(φ1, …, φn) ⇒^τ_s ψ
```

with:

- body `{φ1, …, φn}` — premises,
- head `ψ` — conclusion,
- `τ ∈ {c, r, p}` — norm type,
- `s` — the issuing stakeholder,
- a unique identifier `id`.

| τ | Meaning | Produces |
|---|---------|----------|
| `c` | constitutive | institutional fact |
| `r` | regulative | obligation |
| `p` | permissive | permission |

### 0.3 Arguments (normative detachment)

Given a context `K`, the set of applicable norms produces an **argument**:

```
A = ( Support, hd(A), τ, s )
```

An argument `A` supports the conclusion `hd(A)` using the premises `Support ⊆ K`
(the body of the rule that derives it).

### 0.4 Attacks (contrariety)

Argument `A` attacks argument `B` iff the head of `B` is contrary to the head of `A`:

```
A → B  ⟺  hd(B) ∈ χ(hd(A))
```

The pair `AF = (Args, →)` is the resulting **abstract argumentation framework** (Dung).

### 0.5 Defeats (preference)

A **defeat** is an attack that wins because the attacker is strictly preferred:

```
A ⇒ B  ⟺  A → B  and  hd(A) ≻ hd(B)
```

`≻` is instantiated in two ways:

1. **Priority semantics**: a numeric value per conclusion (the `priorities` section);
   `x ≻ y` iff `priority(x) > priority(y)`.
2. **Classic JAIR semantics**: authority of the issuing **stakeholder**,
   `auth(s)`, derived from `base_priorities` and escalated by `meta_priorities`.
   A norm of stakeholder `s` beats one of `s'` iff `auth(s) > auth(s')`.

### 0.6 Preference/authority derivation (classic JAIR)

Starting from the base authority and the contextual meta-rules:

```
auth(s) = base(s)                                            for every stakeholder s
auth(s) = max( auth(s), value_i )   for each meta-rule i such that trigger_i ∈ E
```

### 0.7 Semantics

The engine implements the standard Dung extension semantics plus a prioritized one:

| Semantics | Extension notion |
|-----------|------------------|
| `naive` | maximal conflict-free set (ignores preferences) |
| `grounded` | least fixed point of the characteristic function (sceptical) |
| `preferred` | maximal admissible set |
| `stable` | admissible set attacking every argument outside it |
| `priority` | defeat-based resolution via the per-conclusion preference `≻` |
| `jiminy` | two-phase normative detachment (classic JAIR) |

### 0.8 The `jiminy` procedure (two-phase detachment)

Given `K`, the procedure returns `(E, P, O)`.

**Phase 1 — institutional closure** (least fixed point):

```
E   ← K
while change:
    for each c-rule r with body(r) ⊆ E:
        E ← E ∪ { head(r) }
```

**Phase 1.5 — authority**:

```
auth(s) ← base(s)
auth(s) ← max( auth(s), value_i )   if trigger_i ∈ E
```

**Phase 2 — permissions**:

```
P ← { head(r) : r is a p-rule with body(r) ⊆ E }
```

**Phase 2 — obligations** (greedy by authority):

```
O ← ∅
while candidates ≠ ∅:
    candidates ← { r is an r-rule :
                    body(r) ⊆ E ∪ P ∪ O   and   head(r) ∉ χ(E ∪ P ∪ O) }
    best ← argmax_{r ∈ candidates} ( auth(stakeholder(r)), id(r) )
    O ← O ∪ { head(best) }
```

The **moral recommendation** is the set of active deontic conclusions `P ∪ O`, and the
accepted heads are `E ∪ P ∪ O`.

---

This document explains, step by step, how the Jiminy engine evaluates the classic JAIR
scenario `scenarios/jair_base.yaml` using the two-phase `compute_jiminy` procedure
(stakeholder-authority semantics, not the per-conclusion `priorities`).

Active brute facts used in this walkthrough:

```
context = [w1, w2, w3, w4]
```

This is the position in which the manufacturer makes the speaker, the speaker collects
data, the collected data indicate a potential threat, and the manufacturer is registered
in Norway.

---

## 1. The scenario

### 1.1 Context (brute facts)

| Fact | Description |
|------|-------------|
| `w1` | the manufacturer makes the smart speaker |
| `w2` | the smart speaker collects user data |
| `w3` | the data collected indicates a potential threat to society |
| `w4` | the manufacturer is a registered company in Norway |

### 1.2 Normative rules

| Id | Type | Body | Conclusion | Stakeholder |
|----|------|------|------------|-------------|
| `c1` | c | `w4` | `i_registered` | Manuf |
| `c2` | c | `w2` | `i_collects_data` | Law |
| `c3` | c | `w3` | `i_threat` | Law |
| `c4` | c | `i_collects_data` | `i_privacy_context` | Household |
| `r1` | r | `w1` | `d_compliant` | Law |
| `r2` | r | `i_registered` | `d_gdpr` | Law |
| `r3` | r | `i_collects_data` | `d_protect_privacy` | Household |
| `r4` | r | `i_threat` | `d_report` | Household |
| `r5` | p | `i_threat` | `d_collect_no_consent` | Manuf |

### 1.3 Stakeholder authority

Base (default) authority of each stakeholder:

```
Law: 5
Household: 2
Manuf: 1
```

Context-dependent authority rules (`meta_priorities`):

| if | stakeholder | value |
|----|-------------|-------|
| `i_collects_data` | Law | 4 |
| `i_threat` | Law | 5 |
| `i_no_threat` | Household | 4 |

The per-conclusion `priorities` section is empty (`priorities: {}`); it is **not used**
by the `jiminy` semantics.

### 1.4 Contrariness (`opposes`)

| Conclusion | Opposes |
|------------|---------|
| `d_gdpr` | `d_collect_no_consent` |
| `d_collect_no_consent` | `d_gdpr`, `d_protect_privacy` |
| `d_protect_privacy` | `d_collect_no_consent` |
| `d_report` | `d_protect_privacy` |
| `d_compliant` | `d_collect_no_consent` |

---

## 2. Execution of `compute_jiminy([w1,w2,w3,w4])`

### 2.1 Phase 1 — Institutional closure

Start with `E = {w1, w2, w3, w4}`. Iteratively fire constitutive norms whose whole body
is in `E`:

1. `c1` (`w4 -> i_registered`): body `{w4}` in `E`. Add `i_registered`.
2. `c2` (`w2 -> i_collects_data`): body `{w2}` in `E`. Add `i_collects_data`.
3. `c3` (`w3 -> i_threat`): body `{w3}` in `E`. Add `i_threat`.
4. `c4` (`i_collects_data -> i_privacy_context`): body `{i_collects_data}` in `E`. Add `i_privacy_context`.

No new constitutive rule fires, so closure is reached:

```
E = { w1, w2, w3, w4, i_registered, i_collects_data, i_threat, i_privacy_context }
```

### 2.2 Phase 1.5 — Derive stakeholder authority

Start from the base priorities, then apply the meta-priority rules whose trigger is in `E`:

- Base: `Law = 5`, `Household = 2`, `Manuf = 1`.
- `i_collects_data in E` -> `Law = max(5, 4) = 5`.
- `i_threat in E` -> `Law = max(5, 5) = 5`.
- `i_no_threat not in E` -> ignored.

Result:

```
stakeholder_priority = { Law: 5, Household: 2, Manuf: 1 }
```

### 2.3 Phase 2 — Permissions

Fire every permissive norm whose body is in `E`:

- `r5` (`i_threat -> d_collect_no_consent`, Manuf): body `{i_threat}` in `E`. Add to `P`.

```
P = { d_collect_no_consent }
```

### 2.4 Phase 2 — Obligations (greedy selection)

We repeatedly pick the regulative norm with the highest stakeholder authority among the
candidates. A candidate must satisfy:

- body is a subset of `E | P | O`, and
- its head is **not** contrary to `E | P | O` (i.e. `head not in contrary_set(E|P|O)`).

Initial `E|P|O = {w1,w2,w3,w4,i_registered,i_collects_data,i_threat,i_privacy_context,d_collect_no_consent}`.

The contrary set of this set is:

```
contrary_set(E|P|O) = contrary(d_collect_no_consent) = { d_gdpr, d_protect_privacy }
```

Candidate regulative norms:

- `r1` (`w1 -> d_compliant`): head `d_compliant` is not contrary. Candidate.
- `r2` (`i_registered -> d_gdpr`): head `d_gdpr` **is** contrary -> skipped.
- `r3` (`i_collects_data -> d_protect_privacy`): head `d_protect_privacy` **is** contrary -> skipped.
- `r4` (`i_threat -> d_report`): head `d_report` is not contrary. Candidate.

Select the candidate with maximal `(stakeholder_priority, id)`:

- `r1` is Law (5), `r4` is Household (2). Max -> `r1`.

Add `d_compliant` to `O`. Repeat:

- `r4` (`d_report`) remains the only candidate. Add `d_report` to `O`.
- No more candidates.

Result:

```
O = { d_compliant, d_report }
```

### 2.5 Final result

```
E = { w1, w2, w3, w4, i_registered, i_collects_data, i_threat, i_privacy_context }
P = { d_collect_no_consent }
O = { d_compliant, d_report }
```

---

## 3. Accepted and rejected

Let `accepted_heads = E | P | O`:

```
accepted: i_registered, i_collects_data, i_threat, i_privacy_context,
          d_collect_no_consent, d_compliant, d_report
rejected: d_gdpr, d_protect_privacy
```

`d_gdpr` and `d_protect_privacy` are generated as arguments from the context, but they are
**skipped** during the obligation phase because their heads are contrary to `d_collect_no_consent`
(the active permission), so they never enter `O`.

### Final moral recommendation

```
Proposed actions: d_collect_no_consent, d_compliant, d_report
```

Meaning:

- `d_compliant` (Law): the manufacturer must comply with applicable laws.
- `d_report` (Household): the detected threat should be reported.
- `d_collect_no_consent` (Manuf, permission): under a threat, the manufacturer may collect
  data without consent.

The key decision is made by **stakeholder authority**, not by a numeric priority of the
conclusion: Law (5) outranks Household (2) and Manuf (1), which is why `d_compliant` is
selected over `d_report` in the first iteration, while `d_gdpr`/`d_protect_privacy` are
defeated by the active permission `d_collect_no_consent`.

---

## 4. Attack and winners graph

The graph below shows the argumentation framework for this situation: red `chi` edges are
attack relations between contradicting heads, and the nodes with a thicker border are the
**winners** (accepted/active decisions). `d_gdpr` and `d_protect_privacy` appear as defeated
attacked nodes.

![Attack and winners graph for jair_base](jair_attack_winners.png)

Observed attacks in the graph:

- `d_compliant` attacks `d_collect_no_consent`.
- `d_collect_no_consent` attacks `d_gdpr`.
- `d_collect_no_consent` attacks `d_protect_privacy`.
- `d_protect_privacy` attacks `d_collect_no_consent`.
- `d_report` attacks `d_protect_privacy`.

Nodes with a double border (`d_compliant`, `d_collect_no_consent`, `d_report` and the
institutional facts) are the accepted recommendations; `d_gdpr` and `d_protect_privacy` are
rejected because they conflict with the active permission.
