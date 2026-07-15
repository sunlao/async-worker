import os
import sys

def count_python_lines(root_dir: str) -> None:
    total_files = 0
    total_lines = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".py"):
                total_files += 1
                file_path = os.path.join(dirpath, f)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    total_lines += sum(1 for _ in fh)
    print(f"Python files: {total_files}")
    print(f"Total lines : {total_lines}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <directory>")
        sys.exit(1)
    count_python_lines(sys.argv[1])
