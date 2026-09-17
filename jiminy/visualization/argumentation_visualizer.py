## @file argumentation_visualizer.py
## @brief Graphviz visualizer for normative argumentation graphs (JAIR style).
"""
Argumentation Visualizer
========================

General-purpose visualization tool for normative argumentation systems
compatible with Jiminy. Produces full JAIR-style representations
including:

 - Arguments (nodes)
 - Attack relations χ (red edges)
 - Defeat-by-priority ≻ (blue edges)
 - Winners / Losers highlighting
 - Stakeholder-based color clusters
 - Automatic legend

Requires: graphviz (apt) AND python graphviz (pip)
"""

from graphviz import Digraph
import colorsys


class ArgumentationVisualizer:
    """
    Visualizer for normative argumentation graphs (JAIR-style).

    Usage:
        viz = ArgumentationVisualizer()
        viz.build_graph(arguments, winners, priorities, contrariness)
        viz.render("agrobot3_graph")
    """

    def __init__(self):
        # Cache to store stakeholder → auto color assignment
        self._stakeholder_colors = {}

    # ------------------------------------------------------------------
    # 1. Utility: Generate distinct colors for stakeholders
    # ------------------------------------------------------------------
    def _get_stakeholder_color(self, name):
        """
        Returns a stable but automatically generated color for a stakeholder.
        Colors are generated in HSL space to maximize distinguishability.
        """
        if name in self.stakeholder_colors:
            return self.stakeholder_colors[name]

        # deterministic hashing to hue
        hue = (hash(name) % 360) / 360.0
        sat = 0.55
        val = 0.95

        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        rgb = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        self.stakeholder_colors[name] = rgb
        return rgb

    # ---------------------------------------------------------------
    # Generate perceptually distinct pastel colors for stakeholders
    # ---------------------------------------------------------------
    def _get_stakeholder_color(self, stakeholder, index=None, total=None):
        """
        Assigns pastel, well-separated colors automatically.
        If index/total provided, uses evenly spaced hues.
        Otherwise, assigns new hues on demand.
        """

        # already assigned?
        if stakeholder in self._stakeholder_colors:
            return self._stakeholder_colors[stakeholder]

        # If index/total provided → deterministic spacing for JAIR-style graphs
        if index is not None and total is not None:
            hue = index / total
        else:
            # fallback: use count
            hue = len(self._stakeholder_colors) * 0.17 % 1.0

        # Convert HSV → RGB (pastel by reducing saturation and increasing value)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.35, 0.95)

        # Convert to hex
        color_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        self._stakeholder_colors[stakeholder] = color_hex
        return color_hex


    # ------------------------------------------------------------------
    # 2. Build graph
    # ------------------------------------------------------------------
    def build_graph(self, arguments, winners, priorities, contrariness):
        """
        Build the internal Graphviz Digraph.

        @param arguments    list of `Argument`.
        @param winners      set of accepted heads (double border).
        @param priorities   dict mapping head -> numeric priority (drives defeats).
        @param contrariness dict mapping head -> set of contrary heads (drives attacks).
        """
        self.graph = Digraph("argumentation", format="png")
        self.graph.attr(rankdir="LR", fontsize="12")

        # Legend
        self._add_legend()

        # First: add all argument nodes
        for arg in arguments:
            self._add_argument_node(arg, winners)

        # Second: add attack edges χ
        # Contrariety is symmetric: if two heads are contrary, both attack
        # each other, so we draw the red attack edge in BOTH directions.
        for A in arguments:
            for contrary in contrariness.get(A.hd, []):
                # We only draw attack edges if the contrary exists
                if any(B.hd == contrary for B in arguments):
                    self._add_attack_edge(A.hd, contrary)
                    self._add_attack_edge(contrary, A.hd)

        # Third: add defeat edges ≻ (based on priorities)
        for A in arguments:
            head = A.hd
            prA = priorities.get(head, 0)

            for contrary in contrariness.get(head, []):
                prC = priorities.get(contrary, 0)

                # A defeats C if A has higher priority
                if prA > prC:
                    # But only draw if both nodes exist
                    if any(B.hd == contrary for B in arguments):
                        self._add_defeat_edge(head, contrary)

    # ------------------------------------------------------------------
    # Add a node
    # ------------------------------------------------------------------
    def _add_argument_node(self, arg, winners):
        """
        Add a node representing an argument:
        - shape and color depend on stakeholder
        - double border if winner
        """
        head = arg.hd
        stakeholder = list(arg.stakeholders)[0]
        color = self._get_stakeholder_color(stakeholder)

        border = "3" if head in winners else "1"

        self.graph.node(
            head,
            label=f"{head}\n({stakeholder})",
            shape="ellipse",
            color=color,
            penwidth=border,
            fontsize="12"
        )

    # ------------------------------------------------------------------
    # Add attack edge (χ)
    # ------------------------------------------------------------------
    def _add_attack_edge(self, src, dst):
        self.graph.edge(
            src,
            dst,
            color="red",
            label="χ",
            fontcolor="red",
            arrowsize="0.9"
        )

    # ------------------------------------------------------------------
    # Add defeat edge (priority-based ≻)
    # ------------------------------------------------------------------
    def _add_defeat_edge(self, winner, loser):
        self.graph.edge(
            winner,
            loser,
            color="blue",
            style="dashed",
            label="≻",
            fontcolor="blue",
            arrowsize="0.9"
        )

    # ------------------------------------------------------------------
    # Legend block
    # ------------------------------------------------------------------
    def _add_legend(self):
        """
        Create a legend inside a subgraph cluster.
        """
        with self.graph.subgraph(name="cluster_legend") as legend:
            legend.attr(label="Legend", fontsize="14", style="rounded", color="black")

            legend.node(
                "legend_attack",
                label="Attack (χ)",
                shape="plaintext"
            )
            legend.node(
                "legend_defeat",
                label="Defeat (≻)",
                shape="plaintext"
            )
            legend.node(
                "legend_winner",
                label="Winner (double border)",
                shape="plaintext"
            )

            # Draw example arrows
            legend.edge("legend_attack", "legend_defeat", color="red", label="χ")
            legend.edge("legend_defeat", "legend_winner", color="blue", style="dashed", label="≻")

    # ------------------------------------------------------------------
    # Render the file
    # ------------------------------------------------------------------
    def render(self, filename="argumentation_graph"):
        """
        Render the graph to disk (a PNG next to the given filename).

        @param filename  output base name (without extension).
        @return  the rendered PNG path.
        """
        print(f"[Visualizer] Rendering graph → {filename}.png")
        self.graph.render(filename, cleanup=True)
        return f"{filename}.png"

