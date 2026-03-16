import os
from textual.widgets import Static
from textual.reactive import reactive
from PIL import Image as PILImage


class GraphPanel(Static):
    """
    Shows the argumentation graph rendered by Graphviz as ASCII art.
    Works even if Textual does not support images natively.
    """

    # Reactive attribute used by TUI: when graph_path changes, the panel updates
    graph_path = reactive(None)

    def on_mount(self):
        # Initial placeholder until first graph is rendered
        self.update("[Graph will appear here]")

    def watch_graph_path(self, path):
        """
        Called automatically whenever graph_path changes.
        If the PNG exists, convert to ASCII; otherwise show placeholder.
        """
        # Added safety: ensure path is non-empty and a string
        if isinstance(path, str) and path and os.path.exists(path):
            ascii_art = self._png_to_ascii(path)
            self.update(ascii_art)
        else:
            self.update("[No graph generated]")

    def _png_to_ascii(self, path, width=80):
        """
        Convert PNG → ASCII using Pillow.

        The ASCII palette is ordered such that:
          - '@' represents darkest pixels
          - ' ' represents brightest pixels

        Resizing is applied to preserve aspect ratio while fitting TUI.
        """
        try:
            img = PILImage.open(path).convert("L")

            # Resize keeping aspect ratio — important for readable ASCII graphs
            wpercent = (width / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((width, hsize))

            chars = "@%#*+=-:. "
            ascii_str = ""

            # Convert each pixel into a character
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    gray = img.getpixel((x, y))
                    ascii_str += chars[int(gray / 255 * (len(chars) - 1))]
                ascii_str += "\n"

            return ascii_str.rstrip("\n")  # avoids trailing whitespace flicker

        except Exception as e:
            # Your original comment kept — adding extended message
            return f"[Error rendering graph: {e}]"
