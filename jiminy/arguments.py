# arguments.py

class Argument:
    """
    Argumento construido mediante detachment.
    """
    def __init__(self, premises, conclusion, origin_norm):
        self.bd = tuple(premises)
        self.hd = conclusion
        self.tau = origin_norm.tau
        self.stakeholders = {origin_norm.stakeholder}
        self.origin_norm = origin_norm

    def __repr__(self):
        return f"A({self.hd}, τ={self.tau}, s={list(self.stakeholders)[0]})"
