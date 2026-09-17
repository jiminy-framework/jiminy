# arguments.py
## @file arguments.py
## @brief Representation of a normative argument built by detachment.

class Argument:
    """
    Argument built via detachment from a norm whose body is satisfied.
    """
    def __init__(self, premises, conclusion, origin_norm):
        """
        @param premises     iterable of support/premises (turned into a tuple `bd`).
        @param conclusion   the head `hd` supported by the argument.
        @param origin_norm  the `Norm` from which the argument was detached.
        """
        self.bd = tuple(premises)
        self.hd = conclusion
        self.tau = origin_norm.tau
        self.stakeholders = {origin_norm.stakeholder}
        self.origin_norm = origin_norm

    def __repr__(self):
        return f"A({self.hd}, τ={self.tau}, s={list(self.stakeholders)[0]})"
