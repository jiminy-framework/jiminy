# norms.py

class Norm:
    """
    Represents a norm of the form:
        (phi1,...,phin) ==>^tau_s psi
    where:
        - body = premises (tuple)
        - head = conclusion psi
        - tau in {"r", "p", "c"}
        - stakeholder = stakeholder identifier
        - id = unique norm identifier (e.g. "H2")
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