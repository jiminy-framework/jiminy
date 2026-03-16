def build_dung_storyboard(
    args,
    accepted,
    rejected,
    attacks,
    priorities,
    contrariness_desc,
):
    lines = []
    step = 1

    # Step 1 — Context
    lines.append("ARGUMENTATION STORYBOARD")
    lines.append("────────────────────────")
    lines.append("")
    lines.append(f"Step {step} — Context analysis")
    lines.append(
        f"The system identified {len(args)} relevant arguments based on the selected context."
    )
    step += 1
    lines.append("")

    # Step 2 — Argument generation
    lines.append(f"Step {step} — Argument generation")
    for a in args:
        lines.append(f"• Argument '{a.hd}' was generated.")
    step += 1
    lines.append("")

    # Step 3 — Conflict detection
    lines.append(f"Step {step} — Conflict detection")
    if attacks:
        for a, b in attacks:
            reason = contrariness_desc.get(
                b, "A normative conflict was detected."
            )
            lines.append(
                f"• Argument '{b}' is challenged by '{a}'. {reason}"
            )
    else:
        lines.append("• No conflicts were detected between arguments.")
    step += 1
    lines.append("")

    # Step 4 — Priority evaluation
    lines.append(f"Step {step} — Priority evaluation")

    for a in accepted:
        pr = priorities.get(a.hd, "unknown")
        lines.append(
            f"• Argument '{a.hd}' was accepted (priority = {pr})."
        )

    for r in rejected:
        pr = priorities.get(r.hd, "unknown")
        lines.append(
            f"• Argument '{r.hd}' was rejected (priority = {pr})."
        )

    step += 1
    lines.append("")


    # Step 5 — Final decision
    lines.append(f"Step {step} — Final decision")
    if accepted:
        actions = [a.hd for a in accepted if not a.hd.startswith("i")]
        if actions:
            lines.append(
                "The system recommends the following actions: "
                + ", ".join(actions) + "."
            )
        else:
            lines.append("No explicit action was recommended.")
    else:
        lines.append("No argument was accepted.")
    lines.append("")

    return "\n".join(lines)
