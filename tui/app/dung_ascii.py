# ================================================================
# ASCII Renderer for Dung-style Argumentation Frameworks
# ================================================================

def ascii_graph(arguments, attacks):
    """
    Produce a simple ASCII visualization of a Dung AF.

    arguments : list of Jiminy Argument objects
    attacks   : list of tuples (attacker, target)

    Returns a multiline string.
    """

    # Extract argument headers
    nodes = [a.hd for a in arguments]

    lines = []
    lines.append("DUNG ARGUMENTATION FRAMEWORK (ASCII)")
    lines.append("====================================")
    lines.append("")

    # List arguments
    lines.append("ARGUMENTS:")
    for n in nodes:
        lines.append(f"  • {n}")
    lines.append("")

    # List attacks
    lines.append("ATTACKS:")
    if attacks:
        for a, b in attacks:
            lines.append(f"  {a}  --->  {b}")
    else:
        lines.append("  (none)")
    lines.append("")

    # Attempt a simple adjacency format
    lines.append("ADJACENCY LIST:")
    adj = {n: [] for n in nodes}
    for a, b in attacks:
        adj[a].append(b)

    for a in nodes:
        targets = ", ".join(adj[a]) if adj[a] else "(none)"
        lines.append(f"  {a}: {targets}")

    lines.append("")
    return "\n".join(lines)
