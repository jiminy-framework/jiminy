# ==============================================================================
# CONTROLLER FOR JIMINY TUI — FINAL WORKING VERSION
# ==============================================================================

from jiminy.yaml_loader import load_scenario
from jiminy import Jiminy
from jiminy.visualization.argumentation_visualizer import ArgumentationVisualizer

class JiminyController:

    def __init__(self, scenario_path):

        (
            self.possible_context,
            self.norms,
            self.contrariness,
            self.priorities,
            self.context_desc,
            self.norm_desc,
            self.contrariness_desc,
            self.priority_desc,
            self.base_priorities,  # New value
            self.meta_priorities   # New value
        ) = load_scenario(scenario_path)

        # Jiminy instancia objetos Norm, no dicts
        self.jim = Jiminy(
            self.norms,
            self.contrariness,
            self.priorities,
            self.context_desc,
            self.norm_desc,
            self.contrariness_desc,
            self.priority_desc,
            self.base_priorities,  # Pass new value
            self.meta_priorities   # Pass new value
        )

        # Estado persistente para el TUI
        self.last_args = []
        self.last_accepted = []
        self.last_rejected = []
        self.last_narrative = ""
        self.last_actions = []
        self.last_args_description = {}
        self.last_graph_path = None


    # ------------------------------------------------------------
    def get_possible_facts(self):
        """Return {fact_id : description}"""
        return self.context_desc


    # ------------------------------------------------------------
    def evaluate(self, active_facts,semantics="priority"):

        try:
            # 1. Argumentos
            args = self.jim.generate_arguments(active_facts)

            # 2. Semántica
            accepted, rejected = self.jim.compute_extension(args, semantics=semantics)

            self.last_args = args
            self.last_accepted = accepted
            self.last_rejected = rejected

            # 3. Explicación
            narrative = self.jim.explain(
                accepted, rejected, active_facts, args, debug=False
            )
            self.last_narrative = narrative

            # 4. Acciones morales
            actions = [A.hd for A in accepted if not A.hd.startswith("i")]
            self.last_actions = actions

            # 5. Generar PNG del grafo
            graph_path = self.render_graph()
            self.last_graph_path = graph_path

            # 6. Descripciones de argumentos
            # 6. Descripciones de argumentos (desde YAML)
            args_description = {
                a.hd: self.norm_desc.get(a.hd, "(sin descripción)")
                for a in args
            }

            self.last_args_description = args_description


            # args_description = {}

            # for a in args:
            #     head = a.hd
            #     desc = "(sin descripción)"

            #     try:
            #         for norm in self.norms:
            #             if getattr(norm, "conclusion", None) == head:
            #                 desc = getattr(norm, "description", "(sin descripción)")
            #                 break
            #     except Exception as e:
            #         desc = f"(error obteniendo descripción: {e})"

            #     args_description[head] = desc

            # self.last_args_description = args_description

            return (
                accepted,
                rejected,
                args,
                narrative,
                actions,
                graph_path,
                args_description,
            )

        except Exception as e:
            return [], [], [], f"[ERROR] {e}", [], None, {}


    # ------------------------------------------------------------
    def render_graph(self):
        """Render Graphviz PNG for arguments."""
        if not self.last_args:
            return None

        viz = ArgumentationVisualizer()
        viz.build_graph(
            arguments=self.last_args,
            winners={A.hd for A in self.last_accepted},
            priorities=self.priorities,
            contrariness=self.contrariness,
        )

        out = "tui_graph.png"
        viz.render(out)
        return out
