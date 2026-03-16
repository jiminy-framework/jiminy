#!/usr/bin/env python3
from tui.app import JiminyTUI
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_tui.py scenarios/candy_unified.yaml")
        sys.exit(1)

    scenario = sys.argv[1]

    app = JiminyTUI(scenario_path=scenario)
    app.run()
