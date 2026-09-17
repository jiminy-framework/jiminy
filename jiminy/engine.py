## @file engine.py
## @brief Jiminy reasoning engine: normative argumentation semantics.

from matplotlib import lines
from .arguments import Argument
from .norms import Norm
import logging
logging.basicConfig(
    level=logging.CRITICAL,              # Show DEBUG and above
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


import time

class Jiminy:
    """
    Jiminy Engine
    =============
    This engine implements the normative argumentation model described in the
    Jiminy Advisor framework.

    The implementation corresponds to the following components in the paper:

      • BRUTE FACTS (K) = context elements
      • INSTITUTIONAL FACTS = results of constitutive norms (τ = c)
      • OBLIGATIONS = results of regulative norms (τ = r)
      • PERMISSIONS = results of permissive norms (τ = p)

      • Argument construction  → Definition of Normative Argument
      • Attack relation        → Conflict via contrariety χ
      • Prioritized extension  → Conflict resolution with preference ordering ≻
      • Explanation            → Transparency layer (not part of formal semantics)
    """

    def __init__(
        self,
        norms,
        contrariness=None,
        priorities=None,
        context_desc=None,
        norm_desc=None,
        contrariness_desc=None,
        priority_desc=None,
        base_priorities=None,
        meta_priorities=None
    ):
        """
        Build a Jiminy reasoning engine from a loaded scenario.

        @param norms            list of `Norm` rules.
        @param contrariness     dict mapping a conclusion to the set of its contraries (chi).
        @param priorities       dict mapping a conclusion to its numeric priority (priority semantics).
        @param context_desc     dict mapping a fact id to its textual description.
        @param norm_desc        dict mapping a norm conclusion to its description.
        @param contrariness_desc dict mapping a conclusion to its contrariety description.
        @param priority_desc    dict mapping a conclusion to its priority description.
        @param base_priorities  dict mapping a stakeholder to its default authority.
        @param meta_priorities  list of context-dependent authority escalation rules
                                ({'if', 'stakeholder', 'value'}).
        """

        self.norms = norms
        self.contrariness = contrariness or {}
        self.priorities = priorities or {}

        self.context_desc = context_desc or {}
        self.norm_desc = norm_desc or {}
        self.contrariness_desc = contrariness_desc or {}
        self.priority_desc = priority_desc or {}

        self.base_priorities = base_priorities or {}
        self.meta_priorities = meta_priorities or []

    # ----------------------------------------------------------------------
    # χ (contrary operator)
    # ----------------------------------------------------------------------
    # Paper mapping:
    #   χ(ψ) gives the set of conclusions incompatible with ψ.
    #   Used to define the attack relation.
    # ----------------------------------------------------------------------
    def contrary(self, x):
        """
        Return the set of conclusions contrary to `x` (the contrariness function chi).

        @param x  a conclusion.
        @return  set(elements) with `set()` if none.
        """
        return self.contrariness.get(x, set())


    # ----------------------------------------------------------------------
    # ARGUMENT CONSTRUCTION  (Detachment)
    # ----------------------------------------------------------------------
    # Paper: Norm detachment / Argument generation
    #
    # A rule:
    #      φ1, …, φn  ⇒^τ_s ψ
    #
    # is applicable iff all φi are true in the current context K.
    #
    # If applicable, it produces a normative argument:
    #      A = (Support = {φ}, Head = ψ)
    #
    # Institutional rules (τ=c) introduce INSTITUTIONAL FACTS.
    # Regulative rules (τ=r) introduce OBLIGATIONS.
    # Permissive rules (τ=p) introduce PERMISSIONS.
    #
    # Resulting conclusions are added to the argument pool for evaluation.
    # ----------------------------------------------------------------------
    # def generate_arguments(self, context):
    #     args = []
    #     for norm in self.norms:
    #         # All rule preconditions must be satisfied
    #         if all(c in context for c in norm.body):
    #             args.append(Argument(norm.body, norm.head, norm))
    #     return args
    # ----------------------------------------------------------------------
    # ARGUMENT CONSTRUCTION with CLOSURE (Fixpoint for constitutive norms)
    # ----------------------------------------------------------------------
    # Paper: constitutive rules must expand the context.
    #
    # Process:
    #  1. Start with brute facts K.
    #  2. Repeatedly apply constitutive norms τ=c to generate institutional facts.
    #  3. Add each new institutional fact to K (closure).
    #  4. After fixpoint, generate all regulative/permissive arguments normally.
    #
    # This ensures rules such as:
    #     w1, w5 -> i1
    #     i1 -> d1
    # activate correctly.
    # ----------------------------------------------------------------------
    def generate_arguments(self, context):
        """
        Generate the normative arguments from a context via detachment.

        Constitutive rules (tau='c') are fired to a fixpoint so that they expand the
        context with institutional facts; then regulative (tau='r') and permissive
        (tau='p') rules are applied to produce obligation/permission arguments.

        @param context  iterable of brute facts (e.g. ['w1', 'w4']).
        @return  list of `Argument` objects.
        """
        context = set(context)   # copy to avoid modifying external reference
        args = []
        changed = True

        # --- FIXPOINT: apply constitutive norms until no new facts appear ---
        while changed:
            changed = False
            for norm in self.norms:
                if norm.tau == "c":  # constitutive rule
                    if all(b in context for b in norm.body):
                        if norm.head not in context:
                            context.add(norm.head)
                            changed = True

                        # Prevent duplicate arguments for same head + premises
                        if not any(
                            a.hd == norm.head and a.bd == tuple(norm.body)
                            for a in args
                        ):
                            args.append(Argument(norm.body, norm.head, norm))


        # --- After closure, generate regulative + permissive arguments ---
        for norm in self.norms:
            if norm.tau != "c":  # r or p
                if all(b in context for b in norm.body):
                    args.append(Argument(norm.body, norm.head, norm))

        return args


    # ----------------------------------------------------------------------
    # ATTACK RELATION (Dung 1995 + Normative Conflicts)
    # ----------------------------------------------------------------------
    # A attacks B  ⟺  head(B) ∈ χ(head(A))
    #
    # That is: the conclusion of argument A is contrary to the conclusion of B.
    #
    # This implements the standard definition of attack in abstract
    # argumentation frameworks extended with contrariety-based conflicts.
    # ----------------------------------------------------------------------
    def attacks(self, A, B):
        """
        True if argument `A` attacks argument `B` (hd(B) in chi(hd(A))).

        @param A  an `Argument`.
        @param B  an `Argument`.
        @return  bool.
        """
        return B.hd in self.contrary(A.hd)


    # ----------------------------------------------------------------------
    # PRIORITIZED EXTENSION
    # ----------------------------------------------------------------------
    # Paper mapping:
    #
    # This corresponds to computing the *justified extension* using a 
    # preference ordering ≻ between conclusions.
    #
    # Procedure implemented here:
    #   1. Group all arguments by their conclusion ψ.
    #   2. For each ψ, collect all contrary conclusions χ(ψ).
    #   3. For the set {ψ} ∪ χ(ψ), determine which conclusion has the highest
    #      priority according to ≻ (given by the priorities dict).
    #   4. Only arguments whose conclusion equals the maximal element survive.
    #
    # FORMAL INTERPRETATION:
    #
    # The line:
    #       best = max(candidates, key=lambda h: priorities[h])
    # corresponds exactly to:
    #
    #       best(ψ) = argmax_{x ∈ {ψ} ∪ χ(ψ)}  ( priority(x) )
    #
    # which is the core of *preference-based defeat* found in:
    #   • Prakken & Sartor
    #   • Makinson & van der Torre (Input/Output logic with priorities)
    #   • Normative reasoning in Jiminy
    #
    # The result is a prioritized extension, i.e., the set of undefeated
    # arguments under the preference ordering.
    # ----------------------------------------------------------------------
    
    # ----------------------------------------------------------------------
    # SELECT EXTENSION SEMANTICS
    # ----------------------------------------------------------------------
    # semantics="priority"   → Prakken/Sartor-style defeat
    # semantics="grounded"   → Dung grounded extension
    # ----------------------------------------------------------------------
    def compute_extension(self, X, semantics="priority"):
        """
        Compute an extension (accepted/rejected arguments) under a semantics.

        @param X          iterable of arguments (or the context for 'naive').
        @param semantics  one of 'priority', 'grounded', 'preferred', 'stable',
                          'preferred_head' or 'naive'.
        @return  (accepted, rejected) lists of `Argument`.
        """

        print(">>> Semantics received:", repr(semantics))

        if semantics == "naive":
            # X must be context, not pre-generated arguments
            context = X
            return self._compute_naive_two_phase(context)

        # For other semantics, X = arguments
        arguments = X

        # print(f">>>>>>>>>>> [TIMING] Semantic computation time")

        start = time.perf_counter()

        if semantics == "grounded":
            accepted, rejected =  self._compute_grounded_extension(arguments)

        elif  semantics == "preferred":
            accepted, rejected =  self._compute_preferred_extension(arguments)

        elif semantics == "preferred_head":
            accepted, rejected =  self._compute_preferred_head_extension(arguments)

        elif semantics == "stable":
            accepted, rejected =  self._compute_stable_extension(arguments)

        else: 
            accepted, rejected = self._compute_priority_extension_B2(arguments, debug=False)
        
        end = time.perf_counter()

        print(f">>>>>>>>>>> [TIMING] Semantic computation time: {end - start:.6f} seconds")

        # Default: Jiminy priority B2 semantics
        return  accepted, rejected

        

    def _compute_priority_extension_B2(self, arguments, debug=False):
        """
        PRIORITY semantics with:
            • local priority comparison (pass 1)
            • losers removed from contraries (B1)
            • REEVALUATION of losers (B2 revival)
            • final defeat propagation among winners

        If debug=True → emit detailed traces via logger.debug().
        """

        # Optionally enable DEBUG temporarily
        if debug:
            previous_level = logger.level
            logger.setLevel(logging.DEBUG)

        logger.debug("\n=== PRIORITY B2 EXTENSION (debug ON) ===")

        # ---------------------------------------------------------------
        # 1. Group arguments by head
        # ---------------------------------------------------------------
        by_head = {}
        for A in arguments:
            by_head.setdefault(A.hd, []).append(A)

        logger.debug("\n[1] GROUPED ARGUMENTS BY HEAD")
        for head, args in by_head.items():
            logger.debug(f"  • {head}: {len(args)} argument(s)")

        # ---------------------------------------------------------------
        # 2. First pass: local priority comparison
        # ---------------------------------------------------------------
        winners = set()
        losers  = set()

        logger.debug("\n[2] FIRST PASS — LOCAL PRIORITY COMPARISON")

        for head, args in by_head.items():
            contrs = [h for h in self.contrary(head) if h in by_head]

            logger.debug(f"\n  Evaluating head: {head}")
            logger.debug(f"    Contraries found: {contrs}")

            if not contrs:
                logger.debug(f"    → WINNER (no contraries)")
                winners.add(head)
                continue

            candidates = [head] + contrs
            best = max(candidates, key=lambda h: self.priorities.get(h, 0))

            logger.debug(f"    Candidates → {candidates}")
            logger.debug(f"    Best: {best} (prio={self.priorities.get(best)})")

            if head == best:
                logger.debug("    → WINNER")
                winners.add(head)
            else:
                logger.debug("    → LOSER")
                losers.add(head)

        logger.debug(f"\n[2.1] WINNERS: {winners}")
        logger.debug(f"[2.1] LOSERS : {losers}")

        # ---------------------------------------------------------------
        # 3 (B1). Clean contraries coming from losers
        # ---------------------------------------------------------------
        cleaned_contraries = {
            h: {c for c in self.contrary(h) if c not in losers}
            for h in by_head
        }

        logger.debug("\n[3] CLEANING CONTRARIES (B1)")
        for h in cleaned_contraries:
            logger.debug(f"  • {h}:")
            logger.debug(f"      original  : {self.contrary(h)}")
            logger.debug(f"      cleaned   : {cleaned_contraries[h]}")

        # ---------------------------------------------------------------
        # 4 (B2). REEVALUATE LOSERS (revival)
        # ---------------------------------------------------------------
        revived = set()

        logger.debug("\n[4] REEVALUATION OF LOSERS (B2 revival)")

        for head in list(losers):
            pr_head = self.priorities.get(head, 0)
            contrs = cleaned_contraries.get(head, set())

            logger.debug(f"\n  Reevaluating: {head}")
            logger.debug(f"    prio={pr_head}, surviving contraries={contrs}")

            defeated = False
            for c in contrs:
                if c in winners and self.priorities.get(c, 0) > pr_head:
                    defeated = True
                    logger.debug(f"      Still defeated by {c} (prio={self.priorities.get(c)})")
                    break

            if not defeated:
                revived.add(head)
                logger.debug("      → REVIVED")
            else:
                logger.debug("      → remains loser")

        winners |= revived
        losers  -= revived

        logger.debug(f"\n[4.1] UPDATED WINNERS: {winners}")
        logger.debug(f"[4.1] UPDATED LOSERS : {losers}")

        # ---------------------------------------------------------------
        # 5. Final defeat propagation among winners
        # ---------------------------------------------------------------
        final_heads = set()

        logger.debug("\n[5] FINAL DEFEAT PROPAGATION")

        for head in winners:
            pr_head = self.priorities.get(head, 0)
            contrs = cleaned_contraries.get(head, set())

            logger.debug(f"\n  Checking {head} (prio={pr_head})")
            logger.debug(f"    contraries={contrs}")

            defeated = False
            for c in contrs:
                if c in winners and self.priorities.get(c, 0) > pr_head:
                    defeated = True
                    logger.debug(f"      → defeated by {c}")
                    break

            if not defeated:
                final_heads.add(head)
                logger.debug("      → ACCEPTED")
            else:
                logger.debug("      → REJECTED")

        logger.debug(f"\n[5.1] FINAL ACCEPTED HEADS: {final_heads}")

        # ---------------------------------------------------------------
        # 6. Build argument list from accepted heads
        # ---------------------------------------------------------------
        selected = [A for A in arguments if A.hd in final_heads]
        rejected = [A for A in arguments if A not in selected]

        logger.debug("\n=== END OF PRIORITY B2 DEBUG ===\n")

        # Restore previous logging level
        if debug:
            logger.setLevel(previous_level)

        return selected, rejected

    def _compute_naive_extension(self, arguments):
        """
        Deterministic Naive extension:
        Builds a maximal conflict-free set by greedily adding arguments
        that do not conflict with the current extension.
        """
        E = set()

        for A in arguments:
            conflict = any(
                self.attacks(A, B) or self.attacks(B, A)
                for B in E
            )
            if not conflict:
                E.add(A)

        return E
    
    def _compute_naive_two_phase(self, context):
        """
        Two-phase Naive semantics (Jiminy-style):
        1. Naive extension over institutional arguments (τ=c)
        2. Regenerate obligations/permissions using the institutional fixpoint
        3. Naive extension again over τ=r/p arguments
        """

        # --- Phase 1: Generate all arguments from context ---
        args = self.generate_arguments(context)

        # Institutional-only arguments
        A_c = [A for A in args if A.origin_norm.tau == "c"]

        # Naive extension on institutional arguments
        E_c = self._compute_naive_extension(A_c)

        # Extract institutional conclusions
        institutional_facts = {A.hd for A in E_c}
    
        # ---------------------------------------------------
        # FIX: naive must NOT discard original context
        #
        # New context is:
        #   original facts  ∪ institutional facts
        # ---------------------------------------------------
        extended_context = set(context) | institutional_facts


        # --- Phase 2: Re-run generation using institutional fixpoint ---
        args2 = self.generate_arguments(extended_context)

        # Select regulative + permissive arguments
        A_rp = [A for A in args2 if A.origin_norm.tau in ("r", "p")]

        # Naive extension on norms (obligations + permissions)
        E_rp = self._compute_naive_extension(A_rp)

        # Combined result
        E_all = set(E_c) | set(E_rp)

        return list(E_all), [A for A in args2 if A not in E_all]



    def _compute_priority_extension_debug(self, arguments):
        """
        PRIORITY semantics with trace.
        Includes:
        - initial local priority comparisons
        - winners and losers
        - defeat propagation
        - final selected arguments
        """

        print("\n=== DEBUG: PRIORITIZED EXTENSION (Instrumented) ===")

        # ---------------------------------------------------------------
        # 1. Group arguments by their conclusion
        # ---------------------------------------------------------------
        by_head = {}
        for A in arguments:
            by_head.setdefault(A.hd, []).append(A)

        print("\n[1] GROUPED ARGUMENTS BY HEAD")
        for head, args in by_head.items():
            print(f"  • {head}: {len(args)} argument(s)")

        # ---------------------------------------------------------------
        # 2. First pass: compute local winners and losers
        # ---------------------------------------------------------------
        print("\n[2] FIRST PASS — LOCAL PRIORITY COMPARISON")

        winners = set()
        losers = set()

        for head, args in by_head.items():
            contrs = [h for h in self.contrary(head) if h in by_head]

            print(f"\n  Evaluating head: {head}")
            print(f"    Contraries found in arguments: {contrs}")

            if not contrs:
                print(f"    → No conflicts. ACCEPTED.")
                winners.add(head)
                continue

            candidates = [head] + contrs
            print(f"    Candidates: {candidates}")

            best = max(candidates, key=lambda h: self.priorities.get(h, 0))
            print(f"    Best by priority: {best} (priority={self.priorities.get(best)})")

            if head == best:
                print(f"    → WINNER: {head}")
                winners.add(head)
            else:
                print(f"    → LOSER: {head}")
                losers.add(head)

        print("\n[2.1] SUMMARY — WINNERS AND LOSERS")
        print("  Winners:", winners)
        print("  Losers :", losers)

        # ---------------------------------------------------------------
        # 3. DEFENSIVE FIX — defeat propagation
        # ---------------------------------------------------------------
        print("\n[3] SECOND PASS — DEFEAT PROPAGATION")

        selected_heads = set()

        for head in winners:
            pr_head = self.priorities.get(head, 0)
            contrs = self.contrary(head)

            print(f"\n  Checking if {head} survives defeat propagation:")
            print(f"    Priority = {pr_head}")
            print(f"    Contraries = {contrs}")

            defeated = False
            for c in contrs:
                if c in winners:
                    pr_c = self.priorities.get(c, 0)
                    print(f"      • Comparing with contrary winner {c} (priority={pr_c})")
                    if pr_c > pr_head:
                        print(f"        → DEFEATED by {c}")
                        defeated = True
                        break

            if not defeated:
                print(f"    → {head} REMAINS ACCEPTED")
                selected_heads.add(head)
            else:
                print(f"    → {head} REMOVED due to stronger contrary")

        print("\n[3.1] HEADS ACCEPTED AFTER PROPAGATION:", selected_heads)

        # ---------------------------------------------------------------
        # 4. Build final selected arguments
        # ---------------------------------------------------------------
        print("\n[4] BUILDING FINAL SELECTED ARGUMENT SET")

        selected = []
        for A in arguments:
            if A.hd in selected_heads:
                print(f"  ✔ Accepting argument: {A.hd} (from {A.bd})")
                selected.append(A)
            else:
                print(f"  ✖ Rejecting argument: {A.hd} (from {A.bd})")

        rejected = [A for A in arguments if A not in selected]

        print("\n=== DEBUG COMPLETED ===\n")
        return selected, rejected


    # ----------------------------------------------------------------------
    # PRIORITIZED EXTENSION  (Default Jiminy semantics)
    # ----------------------------------------------------------------------
    def _compute_priority_extension(self, arguments):
        """
        Minimal prioritized defeat propagation:
        - Select winners by priority.
        - Remove attacks originating from losing conclusions.
        - Re-evaluate acceptance.
        """

        # --- 1. Group arguments by their head ---
        by_head = {}
        for A in arguments:
            by_head.setdefault(A.hd, []).append(A)

        # --- 2. First pass: compute winners (as before) ---
        winners = set()
        losers  = set()

        for head, args in by_head.items():
            conflicting_heads = [
                h for h in self.contrary(head)
                if h in by_head
            ]

            # No conflicts → accepted
            if not conflicting_heads:
                winners.add(head)
                continue

            # Candidates = head + its contraries
            candidates = [head] + conflicting_heads

            # Highest-priority conclusion
            best = max(candidates, key=lambda h: self.priorities.get(h, 0))

            if head == best:
                winners.add(head)
            else:
                losers.add(head)

        # --- 3. DEFENSIVE FIX (minimal propagation of defeat)
        #
        # Any head that was "lost" should NOT be allowed to defeat others.
        #
        # Remove losers from consideration when selecting final accepted arguments.
        #
        # A head is accepted only if:
        #   - it was a winner
        #   - AND none of its contraries are winners with higher priority
        # --------------------------------------------------------------------
        selected = []

        for head, args in by_head.items():

            if head not in winners:
                continue  # already eliminated

            # Check whether any contrary is a stronger winner
            stronger_winner = False
            for c in self.contrary(head):
                if c in winners and self.priorities.get(c, 0) > self.priorities.get(head, 0):
                    stronger_winner = True
                    break

            if not stronger_winner:
                selected.extend(args)

        # Rejected = everything else
        rejected = [A for A in arguments if A not in selected]
        return selected, rejected



    # ----------------------------------------------------------------------
    # GROUNDED SEMANTICS (Dung 1995)
    # ----------------------------------------------------------------------
    def _compute_grounded_extension(self, arguments):
        E = set()
        changed = True

        while changed:
            changed = False

            for A in arguments:
                # Find attackers
                attackers = [B for B in arguments if self._attacks(B, A)]

                # No attackers → accept
                if not attackers:
                    if A not in E:
                        E.add(A)
                        changed = True
                    continue

                # Otherwise must be defended by current E
                defended = all(
                    any(self._attacks(C, B) for C in E)
                    for B in attackers
                )

                if defended and A not in E:
                    E.add(A)
                    changed = True

        rejected = [A for A in arguments if A not in E]
        return list(E), rejected

    def _compute_preferred_head_extension(self, arguments):
        """
        Preferred semantics computed over HEADs with
        priority-based tie-breaking to select a unique extension.
        """

        # --------------------------------------------------
        # 1. Extract HEADs
        # --------------------------------------------------
        heads = sorted({A.hd for A in arguments})

        # --------------------------------------------------
        # 2. Attack relation over HEADs
        # --------------------------------------------------
        def head_attacks(h1, h2):
            return h2 in self.contrary(h1)

        # --------------------------------------------------
        # 3. Conflict-free
        # --------------------------------------------------
        def is_conflict_free(S):
            for h1 in S:
                for h2 in S:
                    if h1 != h2 and head_attacks(h1, h2):
                        return False
            return True

        # --------------------------------------------------
        # 4. Defense
        # --------------------------------------------------
        def defends(S, h):
            attackers = [x for x in heads if head_attacks(x, h)]
            for attacker in attackers:
                defended = any(head_attacks(s, attacker) for s in S)
                if not defended:
                    return False
            return True

        # --------------------------------------------------
        # 5. Admissibility
        # --------------------------------------------------
        def is_admissible(S):
            if not is_conflict_free(S):
                return False
            return all(defends(S, h) for h in S)

        # --------------------------------------------------
        # 6. Enumerate admissible sets
        # --------------------------------------------------
        from itertools import combinations

        admissible_sets = []

        for r in range(len(heads) + 1):
            for combo in combinations(heads, r):
                S = set(combo)
                if is_admissible(S):
                    admissible_sets.append(S)

        # --------------------------------------------------
        # 7. Preferred = maximal admissible
        # --------------------------------------------------
        preferred_sets = [
            S for S in admissible_sets
            if not any(S < T for T in admissible_sets)
        ]

        if not preferred_sets:
            return [], arguments

        # --------------------------------------------------
        # 8. Priority-based tie-breaking
        # --------------------------------------------------
        def total_priority(S):
            return sum(self.priorities.get(h, 0) for h in S)

        best_extension = max(preferred_sets, key=total_priority)

        # --------------------------------------------------
        # 9. Expand to arguments
        # --------------------------------------------------
        accepted_args = [A for A in arguments if A.hd in best_extension]
        rejected_args = [A for A in arguments if A.hd not in best_extension]

        return accepted_args, rejected_args



    # ----------------------------------------------------------------------
    # PREFERRED SEMANTICS (Dung)
    # Computes all maximal admissible sets.
    # ----------------------------------------------------------------------
    def _compute_preferred_extension(self, arguments):
        admissible_sets = []

        # Generate admissible sets
        for S in self._powerset(arguments):
            if self._is_admissible(S, arguments):
                admissible_sets.append(S)

        # Select maximal admissible sets
        preferred_sets = [
            S for S in admissible_sets
            if not any(S < T for T in admissible_sets)
        ]

        if not preferred_sets:
            return [], arguments

        # Jiminy merges all preferred extensions
        accepted = set().union(*preferred_sets)
        rejected = [A for A in arguments if A not in accepted]

        return list(accepted), rejected


    # ----------------------------------------------------------------------
    # STABLE SEMANTICS (Dung)
    # A stable extension S:
    #   - is conflict-free
    #   - attacks every argument not in S
    # ----------------------------------------------------------------------
   
    def _compute_stable_extension(self, arguments):

        # Jiminy semantics: symmetric cycles forbid stable extensions
        if self._has_symmetric_cycle(arguments):
            return [], arguments

        items = list(arguments)
        stable_sets = []

        for S in self._powerset(items):
            if not self._is_conflict_free(S):
                continue
            if not self._attacks_all_outside(S, arguments):
                continue
            stable_sets.append(S)

        if not stable_sets:
            return [], arguments

        # Jiminy: pick the first stable extension; could also union
        accepted = list(stable_sets[0])
        rejected = [A for A in arguments if A not in accepted]

        return accepted, rejected

   

    # ----------------------------------------------------------------------
    # PRIVATE HELPERS
    # ----------------------------------------------------------------------

    def _is_admissible(self, S, arguments):
        """
        An admissible set:
        - is conflict-free
        - defends all its members
        """
        if not self._is_conflict_free(S):
            return False
        return all(self._defends(S, A, arguments) for A in S)


    def _attacks(self, A, B):
        """Return True if argument A attacks B."""
        return B.hd in self.contrary(A.hd)


    def _is_conflict_free(self, S):
        """Conflict-free set check."""
        return all(
            not self._attacks(a, b)
            for a in S for b in S
            if a is not b
        )

    def _defends(self, S, A, arguments):
        """Return True if S defends A against all its attackers."""
        attackers = [B for B in arguments if self._attacks(B, A)]
        return all(
            any(self._attacks(C, B) for C in S)
            for B in attackers
        )


    def _powerset(self, items):
        """Simple powerset."""
        from itertools import combinations
        for r in range(len(items) + 1):
            for combo in combinations(items, r):
                yield set(combo)


    def _attacks_all_outside(self, S, arguments):
        """S attacks every argument outside S."""
        outside = [A for A in arguments if A not in S]
        if not outside:
            return True
        return all(
            any(self._attacks(s, A) for s in S)
            for A in outside
        )

    def _has_symmetric_cycle(self, arguments):
        """Detects A ↔ B symmetric contrariety."""
        for A in arguments:
            for c in self.contrary(A.hd):
                # find argument B with head=c
                B_exists = any(B.hd == c for B in arguments)
                if not B_exists:
                    continue
                # symmetric?
                if A.hd in self.contrary(c):
                    return True
        return False

    def _compute_naive(self, arguments):
        """
        Compute a naive extension deterministically.
        """
        E = set()

        for A in arguments:
            # Check conflict-free condition
            conflict = any(
                self.attacks(A, B) or self.attacks(B, A)
                for B in E
            )
            if not conflict:
                E.add(A)

        return E

    def compute_naive_two_phase(self, context):
        # 1. Generate all arguments
        args = self.generate_arguments(context)

        # Institutional only
        A_c = [A for A in args if A.origin_norm.tau == "c"]

        # First naive extension
        E_c = self._compute_naive(A_c)

        # Collect institutional facts
        facts = {A.hd for A in E_c}

        # Regenerate arguments from institutional fixpoint
        args2 = self.generate_arguments(facts)
        A_rp = [A for A in args2 if A.origin_norm.tau in ("r", "p")]

        # Second naive extension
        E_rp = self._compute_naive(A_rp)

        return E_c, E_rp, E_c | E_rp





    # ----------------------------------------------------------------------
    # EXPLANATION LAYER
    # ----------------------------------------------------------------------
    # Not part of the formal semantics.
    # Provides transparency and human-readable justification.
    # ----------------------------------------------------------------------
    def explain(self, accepted, rejected, context, generated_arguments=None, debug=False, semantics="priority"):

        # Detect naive semantics (the launcher does NOT pass it explicitly)
        # We infer it: if all accepted are c/r/p but we don't use priorities → naive
        # Safer: set by the launcher using an optional attribute.
        is_naive = (semantics == "naive")

        lines = []
        sep = "-" * 60

        # ------------------------------------------------
        # Context
        # ------------------------------------------------
        lines.append(f"CONTEXT ANALYSIS\n{sep}")
        for w in sorted(context):
            if debug and w in self.context_desc:
                lines.append(f" - {w}: {self.context_desc[w]}")
            else:
                lines.append(f" - {w}")
        lines.append("")

        # ------------------------------------------------
        # Arguments
        # ------------------------------------------------
        if generated_arguments is None:
            generated_arguments = self.generate_arguments(context)

        lines.append(f"GENERATED ARGUMENTS\n{sep}")

        for A in generated_arguments:
            s = list(A.stakeholders)[0]
            norm = A.origin_norm
            head = A.hd

            # Tipo
            if head.startswith("i"):
                kind = "Institutional fact"
            elif norm.tau == "r":
                kind = "Obligation"
            elif norm.tau == "p":
                kind = "Permission"
            elif norm.tau == "c":
                kind = "Constitutive norm"
            else:
                kind = "Derived fact"

            if debug:
                desc = self.norm_desc.get(norm.head, "")
                lines.append(
                    f" - {norm.body} ⇒ {head} "
                    f"({kind}, stakeholder={s})  # {desc}"
                )
            else:
                lines.append(
                    f" - {norm.body} ⇒ {head} ({kind}, stakeholder={s})"
                )
        lines.append("")



        # ------------------------------------------------
        # Conflicts
        # ------------------------------------------------
        lines.append(f"DETECTED CONFLICTS\n{sep}")

        for A in generated_arguments:
            if A.hd.startswith("i"):
                continue
            contr = self.contrary(A.hd)
            if contr:
                if debug and A.hd in self.contrariness_desc:
                    lines.append(f" - {A.hd}: {self.contrariness_desc[A.hd]} ↔ {', '.join(contr)}")
                else:
                    lines.append(f" - {A.hd} conflicts with: {', '.join(contr)}")
        lines.append("")


        # ----------------------------------------
        # Priority evaluation (ONLY if NOT naive)
        # ----------------------------------------
        if not is_naive:
            lines.append(f"PRIORITY EVALUATION\n{sep}")
            for A in generated_arguments:
                if A.hd.startswith("i"):
                    continue
                pr = self.priorities.get(A.hd, 0)
                if debug and A.hd in self.priority_desc:
                    lines.append(f" - {A.hd}: {pr}  # {self.priority_desc[A.hd]}")
                else:
                    lines.append(f" - {A.hd}: {pr}")
            lines.append("")


        # ------------------------------------------------
        # Accepted
        # ------------------------------------------------
        lines.append(f"ACCEPTED ARGUMENTS\n{sep}")

        for A in accepted:
            head = A.hd
            if head.startswith("i"):
                lines.append(f" ✔ {head} accepted (institutional fact)")
                continue

            s = list(A.stakeholders)[0]
            if is_naive:
                lines.append(f" ✔ {head} accepted (stakeholder={s})")
            else:
                pr = self.priorities.get(head, 0)
                lines.append(f" ✔ {head} accepted (stakeholder={s}, priority={pr})")


        lines.append("")

        # ------------------------------------------------
        # Rejected
        # ------------------------------------------------
        if not rejected:
            lines.append("No arguments were rejected.\n")
        else:
            for A in rejected:
                s = list(A.stakeholders)[0]
                prA = self.priorities.get(A.hd, 0)

                if is_naive:
                    lines.append(f" ✖ {A.hd} rejected (stakeholder {s})")
                    continue

                lines.append(f" ✖ {A.hd} rejected (stakeholder={s}, priority={prA})")

                contr = self.contrary(A.hd)
                if contr:
                    defeating = [x for x in contr if self.priorities.get(x, 0) > prA]
                    if defeating:
                        lines.append(f"   Defeated by: {', '.join(defeating)}")
                    else:
                        lines.append("   Reason: conflict with superior norms.")
            lines.append("")

        # ------------------------------------------------
        # Final moral recommendation
        # ------------------------------------------------
        final_actions = ", ".join(
            sorted(A.hd for A in accepted if not A.hd.startswith("i"))
        )

        lines.append(f"FINAL MORAL RECOMMENDATION\n{sep}")
        lines.append(f"Proposed actions: {final_actions}")

        
    
        # ------------------------------------------------
        # 9. Narrative Explanation (Optional)
        # ------------------------------------------------
        if debug:
            lines.append("\nNARRATIVE EXPLANATION\n" + sep)

            # Facts in natural language
            facts_text = ", ".join(
                f"{w} ({self.context_desc.get(w, 'no description')})"
                for w in sorted(context)
            )

            # Accepted actions
            # Only moral actions (exclude institutional facts)
            accepted_actions = ", ".join(
                sorted({A.hd for A in accepted if not A.hd.startswith("i")})
            )

            rejected_actions = (
                ", ".join(sorted({A.hd for A in rejected if not A.hd.startswith("i")}))
                if rejected else "none"
            )

            
            if semantics == "naive":

                narrative = (
                    "The robot applies two-phase naive semantics. First, constitutive "
                    "rules are closed under their fixpoint, producing institutional "
                    "facts that define the normative context. Second, obligations and "
                    "permissions are evaluated by selecting a maximal conflict-free set "
                    "of arguments, without using priorities or stakeholder authority. "
                    "The resulting accepted actions represent the non-conflicting "
                    "normative recommendations derived from this two-step reasoning process."
                )

            elif semantics == "jiminy":

                narrative = (
                    f"The robot observes the following contextual facts: {facts_text}. "
                    f"These facts activate constitutive norms that derive institutional "
                    f"facts defining the normative situation. Based on these institutions, "
                    f"meta-norms determine the relative authority of stakeholders. "
                    f"Regulative norms then generate obligations and permissions, and "
                    f"conflicts between them are resolved using structural argumentation "
                    f"semantics guided by stakeholder authority. As a result, the accepted "
                    f"moral actions are: {accepted_actions}. Rejected actions are: "
                    f"{rejected_actions}. The final recommendation reflects the normative "
                    f"outcome derived from the institutional context and the authority "
                    f"structure of the stakeholders involved."
                )

            elif semantics == "preferred":

                narrative = (
                    f"The robot observes the contextual facts: {facts_text}. These facts "
                    f"trigger norms that generate institutional facts, obligations and "
                    f"permissions. Conflicts between arguments are resolved using preferred "
                    f"semantics from abstract argumentation, which selects maximal sets of "
                    f"mutually acceptable arguments. The accepted actions correspond to "
                    f"those supported by the preferred extension of the argumentation "
                    f"framework."
                )

            elif semantics == "grounded":

                narrative = (
                    f"The robot observes the contextual facts: {facts_text}. These facts "
                    f"activate norms that produce arguments representing institutional "
                    f"facts and possible actions. Conflicts between arguments are resolved "
                    f"using grounded semantics, which computes the minimal justified set "
                    f"of arguments. The resulting actions represent the most cautious and "
                    f"skeptically justified recommendations."
                )

            elif semantics == "stable":

                narrative = (
                    f"The robot observes the contextual facts: {facts_text}. Norms generate "
                    f"arguments that may support or attack different actions. Conflicts are "
                    f"resolved using stable semantics, which selects sets of arguments that "
                    f"defeat all arguments outside the set. The accepted actions correspond "
                    f"to those supported by the stable extension of the argumentation "
                    f"framework."
                )

            elif semantics == "priority":

                narrative = (
                    f"The robot observes the contextual facts: {facts_text}. These facts "
                    f"activate norms that generate institutional facts and candidate "
                    f"actions. Conflicts between norms are resolved using explicit priority "
                    f"relations defined in the scenario. Higher-priority norms override "
                    f"conflicting lower-priority norms, producing the final set of "
                    f"accepted actions."
                )


            lines.append(narrative)
            lines.append("")

        return "\n".join(lines)


    # ----------------------------------------------------------------------
    # CAUSAL EXPLANATION
    # ----------------------------------------------------------------------
    def _causal_chain(self, atom):
        """
        Reconstruct the causal derivation chain that produces `atom`.

        Brute facts stop the chain; institutional facts are traced back to the
        constitutive rule that produced them.

        @param atom  a conclusion identifier.
        @return  a human-readable causal string.
        """
        desc = self.context_desc.get(atom) or self.norm_desc.get(atom) or ""
        producing = [n for n in self.norms if n.head == atom]
        if not producing:
            return f"{atom} ({desc})"

        n = producing[0]
        sub = ", ".join(self._causal_chain(b) for b in n.body)
        kind = {"c": "institutional fact", "r": "obligation", "p": "permission"}[n.tau]
        return (
            f"{atom} ({desc}) = {kind} derived by rule {n.id} "
            f"({n.stakeholder}) from [{sub}]"
        )

    def explain_causal(self, accepted, rejected, context, semantics="jiminy"):
        """
        Produce a CAUSAL explanation of every active action.

        For each accepted deontic action it traces the chain of motivating facts,
        institutional facts, the rule and the issuing stakeholder; for each rejected
        action it explains why (conflict with an active conclusion, or not selected).

        @param accepted    list of accepted `Argument`.
        @param rejected    list of rejected `Argument`.
        @param context     the brute facts.
        @param semantics   semantics label (for the header only).
        @return  a human-readable causal explanation string.
        """
        sep = "-" * 60
        lines = [f"CAUSAL EXPLANATION ({semantics})", sep]

        by_head = {}
        for a in accepted:
            by_head.setdefault(a.hd, []).append(a)

        accepted_heads = {a.hd for a in accepted}
        rejected_heads = {a.hd for a in rejected}

        lines.append("\nACTIVE ACTIONS AND WHY THEY ARE MOTIVATED")
        for head in sorted(h for h in accepted_heads if not h.startswith("i")):
            args = by_head.get(head, [])
            if not args:
                continue
            a = args[0]
            n = a.origin_norm
            kind = "obligation" if n.tau == "r" else "permission"
            motiv = ", ".join(self._causal_chain(b) for b in n.body)
            lines.append(f"\n* {head} ({kind}, rule {n.id}, stakeholder {n.stakeholder})")
            lines.append(f"  rule: {tuple(n.body)} =>^{n.tau}_{n.stakeholder} {head}")
            lines.append(f"  why: because {motiv}")

        lines.append(f"\nREJECTED ACTIONS AND WHY")
        for head in sorted(h for h in rejected_heads if not h.startswith("i")):
            conflicts = sorted(
                h for h in accepted_heads if h in self.contrary(head)
            )
            if conflicts:
                reason = f"its conclusion conflicts with the active conclusion(s) {conflicts}"
            else:
                reason = "it was not selected (filtered out or lower stakeholder authority)"
            lines.append(f"\n* {head}: rejected -> {reason}.")

        return "\n".join(lines)


    def compute_jiminy_no_priority(self, context):
        """
        Implementation of Jiminy two-phase semantics WITHOUT priorities,
        directly following the algorithm described in the paper.
        """

        # --------------------------------------------------
        # PHASE 1 — Institutional closure
        # --------------------------------------------------

        E = set(context)
        used = set()

        changed = True
        while changed:
            changed = False

            for norm in self.norms:

                if norm.tau != "c":
                    continue

                if norm in used:
                    continue

                if all(b in E for b in norm.body):

                    # consistency check
                    if norm.head in self.contrary_set(E):
                        continue

                    E.add(norm.head)
                    used.add(norm)
                    changed = True

        # --------------------------------------------------
        # PHASE 2 — Permissions
        # --------------------------------------------------

        P = set()

        for norm in self.norms:

            if norm.tau != "p":
                continue

            if all(b in E for b in norm.body):
                P.add(norm.head)

        # --------------------------------------------------
        # PHASE 2 — Obligations
        # --------------------------------------------------

        O = set()
        used_rules = set()

        changed = True
        while changed:

            changed = False

            for norm in self.norms:

                if norm.tau != "r":
                    continue

                if norm in used_rules:
                    continue

                if not all(b in (E | P | O) for b in norm.body):
                    continue

                # consistency test
                if norm.head in self.contrary_set(E | P | O):
                    continue

                O.add(norm.head)
                used_rules.add(norm)

                changed = True
                break

        return {
            "E": E,
            "P": P,
            "O": O
        }
    
    def contrary_set(self, facts):
        """
        Returns the set of all contraries of the given facts.

        @param facts  iterable of conclusions.
        @return  set of conclusions that are contrary to any of `facts`.
        """
        out = set()

        for f in facts:
            out |= self.contrary(f)

        return out
    
    def compute_jiminy(self, context):
        """
        Classical two-phase Jiminy (JAIR) reasoning procedure.

        Phase 1 computes the institutional closure of constitutive rules; phase 1.5
        derives stakeholder authority from `base_priorities` and `meta_priorities`;
        phase 2 selects permissions and obligations greedily by authority.

        @param context  iterable of brute facts.
        @return  tuple (E, P, O) of institutional facts, permissions and obligations.
        """
        return self._compute_jiminy(context, bidirectional=False)

    def compute_jiminy_bidirectional(self, context):
        """
        Jiminy reasoning with a BIDIRECTIONAL contrariety filter.

        In addition to skipping a regulative rule whose head is already attacked by an
        active element, it also skips a rule whose head ATTACKS an active element. This
        guarantees that whenever there is an attack between an active conclusion and a
        candidate obligation, there is a single winner (the attacking obligation is
        dropped in favour of the active conclusion).

        @param context  iterable of brute facts.
        @return  tuple (E, P, O) of institutional facts, permissions and obligations.
        """
        return self._compute_jiminy(context, bidirectional=True)

    def _compute_jiminy(self, context, bidirectional=False):
        """
        Two-phase Jiminy reasoning core.

        @param context       iterable of brute facts.
        @param bidirectional if True apply the bidirectional contrariety filter.
        @return  tuple (E, P, O).
        """

        # -------------------------------------------------
        # PHASE 1 — Institutional closure
        # -------------------------------------------------

        E = set(context)
        used_rules = set()

        changed = True
        while changed:
            changed = False

            for norm in self.norms:

                if norm.tau != "c":
                    continue

                if norm in used_rules:
                    continue

                if all(b in E for b in norm.body):

                    E.add(norm.head)
                    used_rules.add(norm)
                    changed = True

        # -------------------------------------------------
        # PHASE 1.5 — derive stakeholder priorities
        # -------------------------------------------------

        stakeholder_priority = self._derive_stakeholder_priorities(E)

        # -------------------------------------------------
        # PHASE 2 — permissions
        # -------------------------------------------------

        P = set()

        for norm in self.norms:

            if norm.tau != "p":
                continue

            if all(b in E for b in norm.body):
                P.add(norm.head)

        # -------------------------------------------------
        # PHASE 2 — obligations
        # -------------------------------------------------

        O = set()
        used_rules = set()

        changed = True
        while changed:

            changed = False

            # candidate rules
            candidates = []

            for norm in self.norms:

                if norm.tau != "r":
                    continue

                if norm in used_rules:
                    continue

                if not all(b in (E | P | O) for b in norm.body):
                    continue

                if norm.head in self.contrary_set(E | P | O):
                    continue

                if bidirectional:
                    # Also drop a rule whose head ATTACKS an active element,
                    # so that every attack resolves to a single winner.
                    if set(self.contrary(norm.head)) & (E | P | O):
                        continue

                candidates.append(norm)

            if not candidates:
                break

            # select maximal rule according to stakeholder priority
            # stable tie-break:
            best = max(
                candidates,
                key=lambda n: (
                    stakeholder_priority.get(n.stakeholder, 0),
                    n.id
                )
            )

            O.add(best.head)
            used_rules.add(best)
            changed = True

        return E, P, O
    
    def _derive_stakeholder_priorities_bis(self, E):
        """
        Derive stakeholder priorities dynamically from meta-norms
        defined in the scenario.
        """

        priorities = {}

        # initialize all stakeholders to priority 1
        for norm in self.norms:
            stakeholder = norm.stakeholder
            priorities.setdefault(stakeholder, 1)

        # apply meta-priority rules
        for rule in self.meta_priorities:

            trigger = rule["if"]
            stakeholder = rule["stakeholder"]
            value = rule["value"]

            if trigger in E:
                priorities[stakeholder] = max(priorities.get(stakeholder, 1), value)

        return priorities
    
    def _derive_stakeholder_priorities(self, E):
        """
        Derive stakeholder priorities from base hierarchy
        and contextual meta-priorities.
        """

        priorities = {}

        # -------------------------------------------------
        # base priorities
        # -------------------------------------------------

        for norm in self.norms:
            stakeholder = norm.stakeholder

            base = self.base_priorities.get(stakeholder, 1)
            priorities.setdefault(stakeholder, base)

        # -------------------------------------------------
        # contextual escalation
        # -------------------------------------------------

        for rule in self.meta_priorities:

            trigger = rule["if"]
            stakeholder = rule["stakeholder"]
            value = rule["value"]

            if trigger in E:

                priorities[stakeholder] = max(
                    priorities.get(stakeholder, 1),
                    value
                )

        return priorities
    
