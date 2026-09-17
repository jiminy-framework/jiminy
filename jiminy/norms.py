# norms.py
## @file norms.py
## @brief Representation of a normative rule.

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
        """
        @param body        iterable of premises (turned into a tuple).
        @param head        conclusion psi.
        @param tau         norm type: 'c' (constitutive), 'r' (regulative), 'p' (permissive).
        @param stakeholder the issuing stakeholder identifier.
        @param norm_id     optional unique norm identifier.
        """
        self.body = tuple(body)
        self.head = head
        self.tau = tau
        self.stakeholder = stakeholder
        self.id = norm_id

    @property
    def type(self):
        """
        Return the norm type (alias of `tau`).
        """
        return self.tau

    def __repr__(self):
        label = f"{self.id}: " if self.id else ""
        return f"{label}{self.body} =>^{self.tau}_{self.stakeholder} {self.head}"