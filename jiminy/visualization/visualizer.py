## @file visualizer.py
## @brief Helper visualizer for Jiminy argumentation graphs.
from graphviz import Digraph
import colorsys



class GraphVisualizer:
    """
    Visualisation helper for Jiminy argumentation graphs.
    Provides:
        - Priority/B2 conflict graph
        - JAIR-style semantic graph
    """


    # Base palette (extended automatically if needed)
    BASE_COLORS = [
        "red", "blue", "green", "orange", "purple",
        "brown", "gold", "deeppink", "cyan", "magenta",
        "teal", "navy", "darkgreen", "slateblue"
    ]


    def __init__(self, jiminy_engine):
        self.jim = jiminy_engine


    # ------------------------------------------------------------------
    # Generate stakeholder colors dynamically
    # ------------------------------------------------------------------
    def _compute_stakeholder_colors(self, arguments):
        stakeholders = [
            list(A.stakeholders)[0]
            for A in arguments
        ]
        stakeholders = list(sorted(set(stakeholders)))

        n = len(stakeholders)
        colors = {}

        # If base palette is enough
        if n <= len(self.BASE_COLORS):
            for stk, col in zip(stakeholders, self.BASE_COLORS):
                colors[stk] = col
            return colors

        # Otherwise generate new colors using HSL spacing
        for i, stk in enumerate(stakeholders):
            hue = i / n
            r, g, b = colorsys.hsv_to_rgb(hue, 0.6, 0.9)
            colors[stk] = "#{:02x}{:02x}{:02x}".format(
                int(r*255), int(g*255), int(b*255)
            )

        return colors


    def _stakeholder_color(self, A, color_map):
        stk = list(A.stakeholders)[0]
        return color_map.get(stk, "black")


    # ---------------------------------------------------------------
    #  Graph 3 – PRIORITY with B2 revival + defeat colouring
    # ---------------------------------------------------------------
    def draw_priority_graph(
        self,
        arguments,
        winners,
        revived=None,
        filename="priority_b2_full"
    ):
        revived = revived or set()
        dot = Digraph(format="png")
        dot.attr(rankdir="LR")

        # Generate dynamic stakeholder colors
        stakeholder_colors = self._compute_stakeholder_colors(arguments)

        # Priorities
        pr = {A.hd: self.jim.priorities.get(A.hd, 0) for A in arguments}

        # Detect symmetric cycles
        symmetric_pairs = set()
        for A in arguments:
            for B in arguments:
                if self.jim.attacks(A, B) and self.jim.attacks(B, A):
                    symmetric_pairs.add(tuple(sorted([A.hd, B.hd])))

        # --------------------------------------------------
        # NODES
        # --------------------------------------------------
        for A in arguments:
            color = self._stakeholder_color(A, stakeholder_colors)

            # <<< CHANGED: decision encoded ONLY in node style
            if A.hd in winners:
                dot.node(
                    A.hd,
                    f"{A.hd}\n({list(A.stakeholders)[0]})",
                    shape="ellipse",
                    color=color,
                    penwidth="3"          # double border = accepted
                )
            elif A.hd in revived:
                dot.node(
                    A.hd,
                    f"{A.hd}\n({list(A.stakeholders)[0]})",
                    shape="ellipse",
                    color=color,
                    style="dashed",
                    penwidth="2"
                )
            else:
                dot.node(
                    A.hd,
                    f"{A.hd}\n({list(A.stakeholders)[0]})",
                    shape="ellipse",
                    color="lightgray",
                    penwidth="1"
                )

        # --------------------------------------------------
        # EDGES — ONLY ATTACKS (χ)
        # --------------------------------------------------
        for A in arguments:
            for B in arguments:
                if not self.jim.attacks(A, B):
                    continue

                # <<< CHANGED: cycles explicitly marked
                if tuple(sorted([A.hd, B.hd])) in symmetric_pairs:
                    dot.edge(
                        A.hd,
                        B.hd,
                        color="orange",
                        penwidth="2",
                        label="χ"
                    )
                else:
                    dot.edge(
                        A.hd,
                        B.hd,
                        color="red",
                        penwidth="2",
                        label="χ"
                    )

        # --------------------------------------------------
        # LEGEND
        # --------------------------------------------------
        with dot.subgraph(name="cluster_legend") as legend:
            legend.attr(label="Legend", fontsize="18", style="rounded", color="gray")

            # Relations
            legend.node(
                "L_attack",
                "χ  Attack\n(conflicting arguments)",
                shape="plaintext"
            )

            # Node status
            legend.node(
                "L_win",
                "Accepted argument\n(double border)",
                shape="plaintext"
            )
            legend.node(
                "L_lose",
                "Rejected argument\n(single border)",
                shape="plaintext"
            )
            legend.node(
                "L_rev",
                "Revived argument\n(dashed border)",
                shape="plaintext"
            )

            # Stakeholder colors
            for stk, col in stakeholder_colors.items():
                legend.node(
                    f"stk_{stk}",
                    f"Stakeholder: {stk}",
                    style="filled",
                    fillcolor="white",
                    color=col
                )

        # Export
        dot.render(filename, cleanup=True)
        return filename + ".png"



    # ---------------------------------------------------------------
    #  Graph – JAIR style graph
    # ---------------------------------------------------------------
    def draw_jair_style_graph(self, arguments, winners,
                              filename="jair_style"):
        """
        JAIR-style argumentation graph:
            • Institutional → blue boxes
            • Obligations   → ellipses (black)
            • Permissions   → green hexagons
            • Attacks       → dashed grey
            • Defeats       → bold black
        """

        dot = Digraph(format="png")
        dot.attr(rankdir="LR")

        # Helper to classify arguments by JAIR semantics
        def classify(A):
            if A.origin_norm.tau == "c":
                return "institution"
            elif A.origin_norm.tau == "r":
                return "obligation"
            elif A.origin_norm.tau == "p":
                return "permission"
            else:
                return "fact"

        # --------------------------- NODES ---------------------------
        for A in arguments:
            head = A.hd
            pr = self.jim.priorities.get(head, 0)
            kind = classify(A)

            if kind == "institution":
                dot.node(head, f"{head}\n(p={pr})", shape="box", color="blue")
            elif kind == "obligation":
                dot.node(head, f"{head}\n(p={pr})", shape="ellipse",
                         color="black")
            elif kind == "permission":
                dot.node(head, f"{head}\n(p={pr})", shape="hexagon",
                         color="green")
            else:
                dot.node(head, f"{head}\n(p={pr})", shape="box",
                         color="black")

        # --------------------------- EDGES ---------------------------
        for A in arguments:
            for B in arguments:
                if self.jim.attacks(A, B):

                    # defeat = stronger winner attacking another
                    if (
                        A.hd in winners and
                        self.jim.priorities.get(A.hd, 0) >
                        self.jim.priorities.get(B.hd, 0)
                    ):
                        dot.edge(A.hd, B.hd, color="black", penwidth="3")
                    else:
                        dot.edge(A.hd, B.hd, color="grey", style="dashed")

        dot.render(filename, cleanup=True)
        return filename + ".png"
