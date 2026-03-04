# tests/test_constitutive_acyclicity.py

"""
Verify that the graph induced by constitutive norms is acyclic.

Constitutive rules generate institutional facts. If these rules
form cycles, the institutional closure may become ill-defined.
"""

from jiminy.yaml_loader import load_scenario
import logging
import os

logging.basicConfig(
    level=logging.DEBUG if os.getenv("JIMINY_DEBUG") else logging.INFO
)

logger = logging.getLogger(__name__)

SCENARIO = "scenarios/candy_unified.yaml"


def build_constitutive_graph(norms):
    """
    Build a dependency graph between institutional facts.

    Edge: body_literal -> head
    only for constitutive rules.
    """

    graph = {}

    for n in norms:

        logger.debug("Inspecting norm: %s", n)

        if n.tau != "c":
            logger.debug("Skipping non-constitutive rule: %s", n.id)
            continue

        logger.debug("Processing constitutive rule: %s", n.id)

        for b in n.body:

            logger.debug("Adding dependency: %s -> %s", b, n.head)

            graph.setdefault(b, set())
            graph.setdefault(n.head, set())

            graph[b].add(n.head)

    logger.debug("Generated constitutive graph: %s", graph)

    return graph


def has_cycle(graph):

    visited = set()
    stack = set()

    def dfs(node):

        if node in stack:
            return True

        if node in visited:
            return False

        visited.add(node)
        stack.add(node)

        for neigh in graph.get(node, []):
            if dfs(neigh):
                return True

        stack.remove(node)
        return False

    for n in graph:
        if dfs(n):
            return True

    return False


def test_constitutive_rules_are_acyclic():

    (
        possible_facts,
        norms,
        contrariness,
        priorities,
        context_desc,
        norm_desc,
        contrariness_desc,
        priority_desc
    ) = load_scenario(SCENARIO)

    graph = build_constitutive_graph(norms)

    assert not has_cycle(graph)