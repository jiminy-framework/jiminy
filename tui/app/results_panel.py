from textual.widgets import Static
from textual.reactive import reactive

class ResultsPanel(Static):
    """
    Panel that displays the final accepted arguments and recommendations.
    """

    content = reactive("")

    def update_results(self, accepted, rejected):
        """
        Update panel content based on Jiminy output.
        """
        acc = "\n".join(f"✔ {a.hd}" for a in accepted)
        rej = "\n".join(f"✖ {a.hd}" for a in rejected)

        self.content = (
            "[b]ACCEPTED:[/b]\n"
            f"{acc if acc else '(none)'}\n\n"
            "[b]REJECTED:[/b]\n"
            f"{rej if rej else '(none)'}"
        )

    def render(self):
        return self.content
