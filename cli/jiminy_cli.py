import sys, os
import argparse
import yaml
import subprocess
from jiminy.visualization.visualizer import GraphVisualizer
from jiminy.visualization.argumentation_visualizer import ArgumentationVisualizer


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from jiminy.yaml_loader import load_scenario
from jiminy import Jiminy

from graphviz import Digraph

# ----------------------------------------------------------------------
# Build CLI interface
# ----------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Jiminy scenario launcher")

parser.add_argument("scenario", help="YAML scenario file")

parser.add_argument(
    "--semantics",
    choices=["priority", 
             "grounded", 
             "preferred", 
             "stable", 
             "naive", 
             "preferred_head",
             "jiminy"],
    help="Override semantics to use"
)

parser.add_argument(
    "--facts",
    nargs="*",
    default=None,
    help="List of brute facts active in this run (e.g. --facts w1 w3 w5)"
)

parser.add_argument(
    "--export-af",
    metavar="FILE.dot",
    help="Export the argumentation framework to a DOT file"
)

parser.add_argument(
    "--export-png",
    metavar="FILE.png",
    help="Export the argumentation framework to a PNG image (Graphviz required)"
)

parser.add_argument(
    "--export-graphviz",
    metavar="FILE",
    help="Export argumentation graph using Graphviz layout"
)

args_cli = parser.parse_args()

SCENARIO_PATH = os.path.abspath(args_cli.scenario)

if not os.path.exists(SCENARIO_PATH):
    print(f"ERROR: Scenario file not found: '{SCENARIO_PATH}'")
    sys.exit(1)


# ----------------------------------------------------------------------
# Load YAML (also retrieve semantics if present)
# ----------------------------------------------------------------------
with open(SCENARIO_PATH, "r") as f:
    yaml_data = yaml.safe_load(f)

yaml_semantics = yaml_data.get("semantics", "priority").lower()

# CLI override
semantics = args_cli.semantics if args_cli.semantics else yaml_semantics

if semantics == "jiminy":
    print("[INFO] Using semantics = JIMINY (two-phase normative detachment)")
else:
    print(f"[INFO] Using semantics = {semantics.upper()}")


# ----------------------------------------------------------------------
# Load the formal scenario
# ----------------------------------------------------------------------
(
    possible_context,
    norms,
    contrariness,
    priorities,
    context_desc,
    norm_desc,
    contrariness_desc,
    priority_desc,
    base_priorities,
    meta_priorities
) = load_scenario(SCENARIO_PATH)


# ----------------------------------------------------------------------
# Determine ACTIVE facts
# ----------------------------------------------------------------------
if args_cli.facts is None:
    active_context = possible_context
    print("[INFO] No --facts provided → Using all YAML facts (legacy mode).")
else:
    active_context = args_cli.facts
    print(f"[INFO] Using active facts from CLI: {active_context}")


jim = Jiminy(
    norms,
    contrariness,
    priorities,
    context_desc,
    norm_desc,
    contrariness_desc,
    priority_desc,
    base_priorities,
    meta_priorities
)


# ----------------------------------------------------------------------
# Generate arguments based on ACTIVE facts
# ----------------------------------------------------------------------
args = jim.generate_arguments(active_context)


# ----------------------------------------------------------------------
# Compute extension
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Compute extension
# ----------------------------------------------------------------------

if semantics == "naive":

    accepted, rejected = jim.compute_extension(
        active_context,
        semantics="naive"
    )

elif semantics == "jiminy":

    E, P, O = jim.compute_jiminy(active_context)

    accepted_heads = E | P | O

    args_all = jim.generate_arguments(accepted_heads)

    accepted = [A for A in args_all if A.hd in accepted_heads]
    rejected = [A for A in args_all if A.hd not in accepted_heads]

# elif semantics == "jiminy":

#     result = jim.compute_jiminy_no_priority(active_context)

#     accepted = []
#     rejected = []

#     # Convert heads to arguments
#     all_heads = result["E"] | result["P"] | result["O"]

#     args_all = jim.generate_arguments(all_heads)

#     for A in args_all:
#         if A.hd in result["O"] or A.hd in result["P"] or A.hd in result["E"]:
#             accepted.append(A)
#         else:
#             rejected.append(A)

else:

    accepted, rejected = jim.compute_extension(
        args,
        semantics=semantics
    )
# ----------------------------------------------------------------------
# NEW: Build args_final only for naive semantics
# ----------------------------------------------------------------------
if semantics in ("naive", "jiminy"):
    final_facts = {A.hd for A in accepted}
    args_final = jim.generate_arguments(final_facts)

else:

    args_final = args


# ----------------------------------------------------------------------
# Export AF to DOT
# ----------------------------------------------------------------------
def export_dot(path):
    with open(path, "w") as f:
        f.write("digraph AF {\n")
        f.write('  rankdir="LR";\n')

        # CHANGED: use args_final instead of args
        for A in args_final:
            f.write(f'  "{A.hd}" [shape=box];\n')

        for A in args_final:
            for B in args_final:
                if jim.attacks(A, B):
                    f.write(f'  "{A.hd}" -> "{B.hd}";\n')

        f.write("}\n")

    print(f"[INFO] AF exported to DOT file: {path}")


if args_cli.export_af:
    export_dot(args_cli.export_af)


# ----------------------------------------------------------------------
# Export PNG
# ----------------------------------------------------------------------
if args_cli.export_png:
    dot_file = args_cli.export_png.replace(".png", ".dot")
    export_dot(dot_file)
    print("[INFO] Calling Graphviz to generate PNG...")
    subprocess.run(["dot", "-Tpng", dot_file, "-o", args_cli.export_png])
    print(f"[INFO] AF exported as PNG at: {args_cli.export_png}")


# ----------------------------------------------------------------------
# Print explanation
# ----------------------------------------------------------------------
print(
    jim.explain(
        accepted,
        rejected,
        active_context,
        generated_arguments=args_final,   # CHANGED
        semantics=semantics,
        debug=True
    )
)

def print_decision_legend(norm_desc):

    print("\nDECISION LEGEND")
    print("-" * 60)

    for atom, desc in sorted(norm_desc.items()):

        if atom.startswith("d"):

            if desc:
                print(f"{atom:6} {desc}")
            else:
                print(f"{atom:6}")

    print("\n----------------\n")


print_decision_legend(norm_desc)


# ----------------------------
# GraphVisualizer
# ----------------------------
gv = GraphVisualizer(jim)

gv.draw_priority_graph(
    arguments=args_final,  # CHANGED
    winners={A.hd for A in accepted},
    filename="priority_graph"
)

gv.draw_jair_style_graph(
    arguments=args_final,  # CHANGED
    winners={A.hd for A in accepted},
    filename="jair_graph"
)


# -----------------------------------------
# ArgumentationVisualizer
# -----------------------------------------
try:

    av = ArgumentationVisualizer()

    av.build_graph(
        arguments=args_final,   # CHANGED
        winners={A.hd for A in accepted},
        priorities=jim.priorities,
        contrariness=jim.contrariness
    )

    out_name = SCENARIO_PATH.replace(".yaml", "_graph")
    av.render(out_name)

    print(f"[INFO] Argumentation graph generated: {out_name}.png")

except Exception as e:
    print("[WARN] Could not generate visualization:", e)



def export_graphviz(path):

    g = Digraph("Argumentation Framework", engine="neato")
    g.attr(overlap="false")
    g.attr(splines="true")
    g.attr(splines="spline")

    # General layout
    g.attr(rankdir="TB")
    g.attr(ranksep="1.5")
    g.attr(nodesep="1.0")

    with g.subgraph() as s:
        s.attr(rank="same")
        for A in args_final:
            if A.hd.startswith("i"):
                s.node(A.hd)

    with g.subgraph() as s:
        s.attr(rank="same")
        for A in args_final:
            if A.hd.startswith("d"):
                s.node(A.hd)

    g.attr("node", fontname="Helvetica")
    g.attr("edge", fontname="Helvetica")

    winners = {A.hd for A in accepted}

    # -------------------------------------------------
    # NODES
    # -------------------------------------------------

    for A in args_final:

        if A.hd in winners:
            color = "lightgreen"
        else:
            color = "lightgray"

        g.node(
            A.hd,
            A.hd,
            width="1.2",
            height="0.6",
            shape="box",
            style="filled,rounded",
            fillcolor=color
        )

    # -------------------------------------------------
    # LEVELS (rank)
    # -------------------------------------------------

    with g.subgraph() as s:
        s.attr(rank="same")
        for A in args_final:
            if A.hd.startswith("w"):
                s.node(A.hd)

    with g.subgraph() as s:
        s.attr(rank="same")
        for A in args_final:
            if A.hd.startswith("i"):
                s.node(A.hd)

    with g.subgraph() as s:
        s.attr(rank="same")
        for A in args_final:
            if A.hd.startswith("d"):
                s.node(A.hd)

    # -------------------------------------------------
    # ATTACK EDGES
    # -------------------------------------------------

    for A in args_final:
        for B in args_final:

            if jim.attacks(A, B):

                # winner -> loser
                if A.hd in winners and B.hd not in winners:

                    g.edge(
                        A.hd,
                        B.hd,
                        color="red",
                        penwidth="3",
                        xlabel="defeats",
                        arrowsize="1.2"
                    )

                # attack that does not win
                else:

                    g.edge(
                        A.hd,
                        B.hd,
                        color="red",
                        style="dashed"
                    )

    # -------------------------------------------------
    # RENDER
    # -------------------------------------------------

    g.render(path, format="png", cleanup=True)

    print(f"[INFO] Graphviz graph exported to {path}.png")



def export_reasoning_graph(path):

    g = Digraph("Jiminy Reasoning", engine="dot")

    g.attr(rankdir="TB")
    g.attr(ranksep="1.4")
    g.attr(nodesep="0.7")
    g.attr(splines="spline")

    g.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Helvetica",
        fontsize="11"
    )

    winners = {A.hd for A in accepted}

    facts = set()
    inst = set()
    decisions = set()

    edges = []

    # ------------------------------------------------
    # Collect nodes and edges
    # ------------------------------------------------

    for A in args_final:

        head = A.hd

        if head.startswith("w"):
            facts.add(head)

        elif head.startswith("i"):
            inst.add(head)

        elif head.startswith("d"):
            decisions.add(head)

        if not hasattr(A, "norm") or not A.norm:
            continue

        body = getattr(A.norm, "body", [])

        for b in body:

            edges.append((b, head))

            if b.startswith("w"):
                facts.add(b)

            elif b.startswith("i"):
                inst.add(b)

            elif b.startswith("d"):
                decisions.add(b)

    # ------------------------------------------------
    # Label builder
    # ------------------------------------------------

    def build_label(lit):

        if lit in context_desc:
            text = context_desc[lit]

        elif lit in norm_desc:
            text = norm_desc[lit]

        else:
            text = ""

        if text:
            return f"{lit}\\n{text}"

        return lit

    # ------------------------------------------------
    # Nodes
    # ------------------------------------------------

    for w in facts:

        g.node(
            w,
            label=build_label(w),
            fillcolor="lightblue"
        )

    for i in inst:

        g.node(
            i,
            label=build_label(i),
            fillcolor="lightgreen"
        )

    for d in decisions:

        if d in winners:
            color = "orange"      # accepted decision
        else:
            color = "lightgray"   # rejected decision

        g.node(
            d,
            label=build_label(d),
            fillcolor=color
        )

    # ------------------------------------------------
    # Edges (reasoning support)
    # ------------------------------------------------

    for a, b in edges:

        g.edge(
            a,
            b,
            color="blue",
            penwidth="2",
            arrowsize="0.9"
        )

    # ------------------------------------------------
    # Layers
    # ------------------------------------------------

    with g.subgraph() as s:
        s.attr(rank="same")
        for w in facts:
            s.node(w)

    with g.subgraph() as s:
        s.attr(rank="same")
        for i in inst:
            s.node(i)

    with g.subgraph() as s:
        s.attr(rank="same")
        for d in decisions:
            s.node(d)


    # ------------------------------------------------
    # LEGEND (boxed and forced at bottom)
    # ------------------------------------------------

    with g.subgraph(name="legend_rank") as bottom:

        bottom.attr(rank="sink")

        bottom.node("legend_anchor", style="invis")

        with bottom.subgraph(name="cluster_legend") as legend:

            legend.attr(label="Legend")
            legend.attr(style="rounded")
            legend.attr(color="gray50")
            legend.attr(fontname="Helvetica")
            legend.attr(fontsize="12")

            legend.node(
                "l_fact",
                "[Fact]",
                fillcolor="lightblue",
                style="rounded,filled",
                shape="box"
            )

            legend.node(
                "l_inst",
                "[Institutional Fact]",
                fillcolor="lightgreen",
                style="rounded,filled",
                shape="box"
            )

            legend.node(
                "l_acc",
                "Accepted decision",
                fillcolor="orange",
                style="rounded,filled",
                shape="box"
            )

            legend.node(
                "l_rej",
                "Rejected decision",
                fillcolor="lightgray",
                style="rounded,filled",
                shape="box"
            )

            legend.node(
                "l_support",
                "Reasoning support",
                shape="plaintext"
            )

            legend.edge(
                "l_fact",
                "l_support",
                color="blue",
                penwidth="2"
            )

    # ------------------------------------------------
    # Render
    # ------------------------------------------------

    g.render(path, format="png", cleanup=True)

    print(f"[INFO] Reasoning graph exported to {path}.png")

def export_defeat_graph(path):

    g = Digraph("Jiminy Defeat", engine="dot")

    g.attr(rankdir="LR")
    g.attr(splines="curved")
    g.attr(nodesep="0.8")

    g.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Helvetica"
    )

    winners = {A.hd for A in accepted}

    # -----------------------------
    # NODES
    # -----------------------------

    for A in args_final:

        if not A.hd.startswith("d"):
            continue

        color = "lightgreen" if A.hd in winners else "lightgray"

        g.node(A.hd, fillcolor=color)

    # -----------------------------
    # ATTACK EDGES
    # -----------------------------

    for A in args_final:
        for B in args_final:

            if not A.hd.startswith("d"):
                continue

            if not B.hd.startswith("d"):
                continue

            if jim.attacks(A, B):

                if A.hd in winners and B.hd not in winners:

                    g.edge(
                        A.hd,
                        B.hd,
                        color="red",
                        penwidth="3",
                        arrowsize="1.2",
                        xlabel="defeats"
                    )

                else:

                    g.edge(
                        A.hd,
                        B.hd,
                        color="red",
                        style="dashed"
                    )

    g.render(path, format="png", cleanup=True)

    print(f"[INFO] Defeat graph exported to {path}.png")


def build_label(atom):

    if atom in context_desc:
        return f"{atom}\n[Fact]\n{context_desc[atom]}"

    if atom in norm_desc:
        return f"{atom}\n[Norm]\n{norm_desc[atom]}"

    return atom


def build_label(atom):

    if atom.startswith("w"):
        return f"{atom}\n[Fact]\n{context_desc.get(atom,'')}"

    if atom.startswith("i"):
        return f"{atom}\n[Institution]\n{norm_desc.get(atom,'')}"

    if atom.startswith("d"):
        return f"{atom}\n[Decision]\n{norm_desc.get(atom,'')}"

    return atom


if args_cli.export_graphviz:
    export_graphviz(args_cli.export_graphviz)
    export_reasoning_graph("jiminy_reasoning")
    export_defeat_graph("jiminy_defeat")