#!/usr/bin/env python3
"""
Space Shooter — terminal game
Requires Python 3.6+ with the standard `curses` library (Linux/macOS).

Run:
    python main.py
"""
import curses
import sys


def main():
    if sys.platform == "win32":
        print("This game requires a Unix-compatible terminal (Linux/macOS).")
        print("On Windows, try running inside WSL.")
        sys.exit(1)
    try:
        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing Space Shooter!")


def _run(stdscr):
    from game import Game
    Game(stdscr).run()


if __name__ == "__main__":
    main()
