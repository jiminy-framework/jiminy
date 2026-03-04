# norms.py

class Norm:
    """
    Representa una norma de la forma:
        (φ1,...,φn) ==>^τ_s ψ
    donde:
        - body = premisas (tuple)
        - head = conclusión ψ
        - tau ∈ {"r", "p", "c"}
        - stakeholder = identificador del stakeholder
        - id = identificador único de la norma (p.ej. "H2")
    """
    def __init__(self, body, head, tau, stakeholder, norm_id=None):
        self.body = tuple(body)
        self.head = head
        self.tau = tau
        self.stakeholder = stakeholder
        self.id = norm_id

    @property
    def type(self):
        return self.tau

    def __repr__(self):
        label = f"{self.id}: " if self.id else ""
        return f"{label}{self.body} =>^{self.tau}_{self.stakeholder} {self.head}"