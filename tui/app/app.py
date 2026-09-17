# ==============================================================================
# TUI APPLICATION FOR JIMINY — WORKING VERSION
# ==============================================================================

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer
from textual.binding import Binding

from .dung_ascii import ascii_graph

from .dung_storyboard import build_dung_storyboard


from .controller import JiminyController
from .panels import (
    FactsPanel,
    ArgumentationPanel,
    ActionsPanel,
    NarrativePanel,
    GraphPanel,
    HelpPanel,
    DungGraphPanel
)
from .messages import UpdateFacts, ShowEvaluation


class JiminyTUI(App):

    CSS_PATH = "jiminy_ui.tcss"

    BINDINGS = [
        Binding("space", "evaluate", "Evaluate"),
        Binding("e", "evaluate", "Evaluate"),
        Binding("g", "graph_png", "Graph PNG→ASCII"),
        Binding("d", "dung_ascii", "Dung - ASCII Mode "),
        Binding("s", "dung_storyboard", "Dung - Storyboard Mode"),
        Binding("n", "set_semantics_naive", "Semantics: NAIVE"),     
        Binding("p", "set_semantics_priority", "Semantics: PRIORITY"),  
        Binding("r", "reset", "Reset"),
        Binding("q", "quit", "Quit"),
        
    ]

    def __init__(self, scenario_path):
        super().__init__()
        self.current_semantics = "priority"
        self.controller = JiminyController(scenario_path)

    def compose(self) -> ComposeResult:

        facts = FactsPanel(self.controller.get_possible_facts(), id="facts_panel")
        argumentation = ArgumentationPanel(id="argumentation_panel")
        actions = ActionsPanel(id="actions_panel")
        narrative = NarrativePanel(id="narrative_panel")
        graph = GraphPanel(id="graph_panel")
        dung = DungGraphPanel(id="dung_panel")

        yield Horizontal(
            facts,
            Vertical(
                argumentation,
                actions,
                narrative,
                graph,
                dung,
                id="right-side"
            )
        )

        yield HelpPanel()
        yield Footer()


    # ----------------------------------------------------------------------
    # ACTION: Evaluate (SPACE)
    # ----------------------------------------------------------------------
    async def action_evaluate(self):

        facts_panel = self.query_one("#facts_panel")
        active = [fid for fid, cb in facts_panel.checkboxes.items() if cb.value]

        (
            accepted,
            rejected,
            args,
            narrative,
            actions,
            graph_path,
            args_desc,
        ) = self.controller.evaluate(
            active,
            semantics=self.current_semantics
        )

        # Dung graph is generated later with the D key, not now.
        ascii_dung = None

        self.post_message(
            ShowEvaluation(
                accepted=accepted,
                rejected=rejected,
                args=args,
                narrative=narrative,
                actions=actions,
                graph_path=graph_path,
                args_description=args_desc,
                ascii_graph=ascii_dung
            )
        )


    # ----------------------------------------------------------------------
    # ACTION: Show ASCII of Graphviz PNG (G)
    # ----------------------------------------------------------------------
    async def action_graph_png(self):

        # We use the last results without overwriting anything
        accepted = self.controller.last_accepted
        rejected = self.controller.last_rejected
        args = self.controller.last_args
        narrative = self.controller.last_narrative
        actions = self.controller.last_actions
        graph_path = self.controller.last_graph_path
        args_desc = self.controller.last_args_description

        # We don't generate ASCII Dung here
        ascii_dung = None

        self.post_message(
            ShowEvaluation(
                accepted=accepted,
                rejected=rejected,
                args=args,
                narrative=narrative,
                actions=actions,
                graph_path=graph_path,
                args_description=args_desc,
                ascii_graph=ascii_dung,
            )
        )

    # ----------------------------------------------------------------------
    # ACTION: Set semantics NAIVE
    # ----------------------------------------------------------------------
    async def action_set_semantics_naive(self):
        self.current_semantics = "naive"
        self.notify("Semantics set to NAIVE")
        await self.action_evaluate()    # <<< re-evaluate


    # ----------------------------------------------------------------------
    # ACTION: Set semantics PRIORITY
    # ----------------------------------------------------------------------
    async def action_set_semantics_priority(self):
        self.current_semantics = "priority"
        self.notify("Semantics set to PRIORITY")
        await self.action_evaluate()


    # ----------------------------------------------------------------------
    # ACTION: Dung ASCII graph (D)
    # ----------------------------------------------------------------------
    async def action_dung_ascii(self):

        accepted = self.controller.last_accepted
        args = self.controller.last_args
        contr = self.controller.contrariness

        if not args:
            ascii_txt = "(No arguments available)"
        else:
            attacks = []
            for a in args:
                for b in args:
                    if b.hd in contr.get(a.hd, []):
                        attacks.append((a.hd, b.hd))

            ascii_txt = ascii_graph(args, attacks)

        self.post_message(
            ShowEvaluation(
                accepted=self.controller.last_accepted,
                rejected=self.controller.last_rejected,
                args=self.controller.last_args,
                narrative=self.controller.last_narrative,
                actions=self.controller.last_actions,
                graph_path=self.controller.last_graph_path,
                args_description=self.controller.last_args_description,
                ascii_graph=ascii_txt,
            )
        )



    # ----------------------------------------------------------------------
    # ACTION: Reset UI (R)
    # ----------------------------------------------------------------------
    async def action_reset(self):

        facts_panel = self.query_one("#facts_panel")

        for cb in facts_panel.checkboxes.values():
            cb.value = False

        self.query_one("#argumentation_panel").update("(cleared)")
        self.query_one("#actions_panel").update("(cleared)")
        # self.query_one("#narrative_panel").update("(cleared)")
        self.query_one("#narrative_panel").clear() 
        self.query_one("#graph_panel").update("[Graph will appear here]")
        # self.query_one("#dung_panel").update("(press D to generate ASCII AF)")
        self.query_one("#dung_panel").clear()
        




    async def action_dung_storyboard(self):

        args = self.controller.last_args
        accepted = self.controller.last_accepted
        rejected = self.controller.last_rejected
        contr = self.controller.contrariness
        priorities = self.controller.priorities
        contr_desc = self.controller.contrariness_desc

        if not args:
            storyboard = "(No arguments available)"
        else:
            # rebuild attacks (same as in Dung ASCII)
            attacks = []
            for a in args:
                for b in args:
                    if b.hd in contr.get(a.hd, []):
                        attacks.append((a.hd, b.hd))

            storyboard = build_dung_storyboard(
                args=args,
                accepted=accepted,
                rejected=rejected,
                attacks=attacks,
                priorities=priorities,
                contrariness_desc=contr_desc,
            )

        self.post_message(
            ShowEvaluation(
                accepted=accepted,
                rejected=rejected,
                args=args,
                narrative=self.controller.last_narrative,
                actions=self.controller.last_actions,
                graph_path=self.controller.last_graph_path,
                args_description=self.controller.last_args_description,
                ascii_graph=storyboard,   # 👈 reuse the magenta panel
            )
        )


    # ----------------------------------------------------------------------
    # ACTION: Quit
    # ----------------------------------------------------------------------
    async def action_quit(self):
        self.exit()


    # ----------------------------------------------------------------------
    # MESSAGE ROUTING
    # ----------------------------------------------------------------------
    async def on_show_evaluation(self, message: ShowEvaluation):

        self.query_one("#argumentation_panel").post_message(message)
        self.query_one("#actions_panel").post_message(message)
        self.query_one("#narrative_panel").post_message(message)
        self.query_one("#graph_panel").post_message(message)
        self.query_one("#dung_panel").post_message(message)


