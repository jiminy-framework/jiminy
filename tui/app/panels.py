# ==============================================================================
# PANELS FOR JIMINY TUI — FACTS / ARGUMENTS / ACTIONS / NARRATIVE / GRAPH
# ==============================================================================

from textual.widgets import Checkbox, Static
from textual.containers import Vertical, VerticalScroll
from .messages import UpdateFacts, ShowEvaluation
import os
from PIL import Image as PILImage

# ------------------------------------------------------------------------------
# FACTS PANEL
# ------------------------------------------------------------------------------
class FactsPanel(Static):

    def __init__(self, facts_dict, **kwargs):
        super().__init__(**kwargs)
        self.facts_dict = facts_dict
        self.checkboxes = {}

    def compose(self):
        with Vertical():
            for fid, desc in self.facts_dict.items():
                cb = Checkbox(f"{fid} – {desc}")
                self.checkboxes[fid] = cb
                yield cb

    def on_checkbox_changed(self, event: Checkbox.Changed):
        active = [fid for fid, cb in self.checkboxes.items() if cb.value]
        self.post_message(UpdateFacts(active))


# ------------------------------------------------------------------------------
# ARGUMENTATION PANEL
# ------------------------------------------------------------------------------
class ArgumentationPanel(Static):

    def on_show_evaluation(self, msg: ShowEvaluation):
        # ← PREVENTS THE ERROR THAT EMPTIES EVERYTHING
        args_desc = getattr(msg, "args_description", {}) or {}

        def fmt(a):
            d = args_desc.get(a.hd, "(no description)")
            return f"- [b]{a.hd}[/b] — {d}"

        accepted = "\n".join(fmt(a) for a in msg.accepted) or "(none)"
        rejected = "\n".join(fmt(a) for a in msg.rejected) or "(none)"

        self.update(
            "[b]ACCEPTED:[/b]\n"
            f"{accepted}\n\n"
            "[b]REJECTED:[/b]\n"
            f"{rejected}"
        )


# ------------------------------------------------------------------------------
# ACTIONS PANEL
# ------------------------------------------------------------------------------
class ActionsPanel(Static):

    def on_show_evaluation(self, msg: ShowEvaluation):
        out = "[b]MORAL ACTIONS[/b]\n"
        out += "\n".join(f"- {a}" for a in msg.actions) or "(none)"
        self.update(out)


# ------------------------------------------------------------------------------
# NARRATIVE PANEL
# ------------------------------------------------------------------------------
class NarrativePanel(VerticalScroll):
    """
    Scrollable panel for the explanatory narrative.
    """

    def on_mount(self):
        self.content = Static("[b]Narrative[/b]\n\n(none)")
        self.mount(self.content)

    def on_show_evaluation(self, msg: ShowEvaluation):
        self.content.update(
            "[b]Narrative[/b]\n\n"
            f"[i]Semantics: {self.app.current_semantics.upper()}[/i]\n\n"
            + (msg.narrative or "(none)")
        )
    
    def clear(self):
        self.content.update("[b]Narrative[/b]\n\n(cleared)")


# ------------------------------------------------------------------------------
# GRAPH PANEL (PNG → ASCII)
# ------------------------------------------------------------------------------
class GraphPanel(Static):

    def on_show_evaluation(self, msg: ShowEvaluation):
        # Dung ASCII takes priority if present
        self.update_graph(msg.graph_path)

    def update_graph(self, path):
        if not path or not os.path.exists(path):
            self.update("[Graph not generated]")
            return
        self.update(self._png_to_ascii(path))

    def _png_to_ascii(self, path, width=80):
        try:
            img = PILImage.open(path).convert("L")
            wpercent = width / img.size[0]
            hsize = int(img.size[1] * wpercent)
            img = img.resize((width, hsize))
            chars = "@%#*+=-:. "
            out = ""
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    gray = img.getpixel((x, y))
                    idx = int(gray / 255 * (len(chars) - 1))
                    out += chars[idx]
                out += "\n"
            return out
        except Exception as e:
            return f"[Error rendering ASCII graph: {e}]"


# ------------------------------------------------------------------------------
# DUNG ASCII PANEL
# ------------------------------------------------------------------------------


class DungGraphPanel(VerticalScroll):
    """
    Scrollable panel that shows the Dung AF in ASCII.
    """

    def on_mount(self):
        # Internal widget where the text is actually drawn
        self.content = Static("(press 'd' to generate Dung AF ascii graph)")
        self.mount(self.content)

    def on_show_evaluation(self, msg: ShowEvaluation):
        if msg.ascii_graph:
            self.content.update(
                "[b]DUNG ARGUMENTATION FRAMEWORK (ASCII)[/b]\n\n"
                + msg.ascii_graph
            )
        else:
            self.content.update("(press 'd' to generate Dung AF ascii graph)")

    def clear(self):
        self.content.update("[b]DUNG[/b]\n\n(cleared)")



# ------------------------------------------------------------------------------
# HELP PANEL
# ------------------------------------------------------------------------------
class HelpPanel(Static):

    def on_mount(self):
        self.update(
            "[b][SPACE][/b] Evaluate   "
            "[b][G][/b] Graph (PNG→ASCII)   "
            "[b][D][/b] Dung ASCII   "
            "[b][R][/b] Reset   "
            "[b][Q][/b] Quit"
        )