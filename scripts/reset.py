#!/usr/bin/env python3
"""
reset.py — project root reset utility

Deletes transient artifacts:
- *.log from ./logs
"""

import os
import glob

def remove(patterns):
    for pattern in patterns:
        for path in glob.glob(pattern):
            try:
                os.remove(path)
                print(f"deleted: {path}")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"error deleting {path}: {e}")

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    targets = [
        f"{root}/logs/*.log",
        f"{root}/logs/*.gz",
        f"{root}/tests/.coverage*",
    ]

    remove(targets)
    print("reset complete.")
