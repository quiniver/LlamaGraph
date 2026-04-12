#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — llamagraph entry point

Parses CLI arguments, creates the Tkinter root, builds the MainWindow,
instantiates the Presenter (which wires everything together), and starts
the event loop.

This file should stay minimal: orchestration logic lives in the Presenter.
"""

import argparse
import sys
from pathlib import Path

import tkinter as tk

from view.main_window import MainWindow
from presenter.plotter_presenter import PlotterPresenter
from utils.colors import DEFAULT_PP_COLOR, DEFAULT_TG_COLOR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="llamagraph — llama-bench benchmark visualizer"
    )
    parser.add_argument(
        'directory',
        nargs='?',
        type=Path,
        default=Path('.'),
        help="Directory containing llama-bench CSV files (default: current dir)",
    )
    parser.add_argument(
        '--ns',
        action='store_true',
        help="Start in latency (ns) view instead of tokens/s",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.directory.exists():
        print(f"Error: directory '{args.directory}' does not exist.", file=sys.stderr)
        sys.exit(1)

    root = tk.Tk()

    # Build the window (View layer)
    window = MainWindow(
        root,
        pp_color=DEFAULT_PP_COLOR,
        tg_color=DEFAULT_TG_COLOR,
    )

    # Instantiate the Presenter (wires Model ↔ View, scans files)
    _presenter = PlotterPresenter(
        window=window,
        start_dir=args.directory,
        pp_color=DEFAULT_PP_COLOR,
        tg_color=DEFAULT_TG_COLOR,
        default_ts=not args.ns,
    )

    root.mainloop()


if __name__ == "__main__":
    main()