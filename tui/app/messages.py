# ======================================================================
# CUSTOM MESSAGES FOR THE JIMINY TUI
# ======================================================================

from textual.message import Message


class UpdateFacts(Message):
    """Message emitted when checkboxes of facts change."""
    def __init__(self, active_facts):
        super().__init__()
        self.active_facts = active_facts


class ShowEvaluation(Message):
    """
    Message broadcast after evaluating Jiminy.

    Contains:
        - accepted arguments
        - rejected arguments
        - raw arguments
        - actions
        - narrative text
        - graph_path
        - args_description (NEW)
    """
    MESSAGE_ID = "showevaluation"

    def __init__(
        self,
        accepted,
        rejected,
        args,
        narrative,
        actions,
        graph_path,
        args_description,   # <<<<<<<<<< NEW FIELD
        ascii_graph=None,       # <<<<<<<<<< NEW FIELD
    ):
        super().__init__()
        self.accepted = accepted
        self.rejected = rejected
        self.args = args
        self.narrative = narrative
        self.actions = actions
        self.graph_path = graph_path
        self.args_description = args_description  # <<<<<<<<<< STORE FIELD
        self.ascii_graph = ascii_graph
