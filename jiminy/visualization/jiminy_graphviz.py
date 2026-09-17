## @file jiminy_graphviz.py
## @brief Standalone Graphviz renderer for a Jiminy argumentation graph.
from graphviz import Digraph

def render_argument_graph(arguments, attacks, accepted, filename="jiminy_graph"):
    """
    Render an argumentation graph to a PNG file.

    @param arguments  iterable of argument labels (nodes).
    @param attacks    iterable of (attacker, attacked) attack pairs.
    @param accepted   iterable of accepted labels (filled lightgreen).
    @param filename   output base name (without extension).
    @return  the rendered PNG path.
    """
    g = Digraph("Jiminy Argumentation", engine="dot")

    g.attr(rankdir="TB")   # Top → Bottom layout

    # -----------------------------
    # NODES
    # -----------------------------

    for arg in arguments:

        if arg in accepted:
            color = "lightgreen"
        else:
            color = "lightgray"

        g.node(
            arg,
            arg,
            style="filled,rounded",
            fillcolor=color,
            shape="box"
        )

    # -----------------------------
    # ATTACK EDGES
    # -----------------------------

    for a,b in attacks:

        if a in accepted and b not in accepted:

            g.edge(
                a,b,
                color="red",
                penwidth="2"
            )

        else:

            g.edge(
                a,b,
                color="red",
                style="dashed"
            )

    # -----------------------------
    # SAVE GRAPH
    # -----------------------------

    g.render(filename, format="png", cleanup=True)