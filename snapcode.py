import os
from datetime import datetime

VERSION_FILE = "codebase_extrator/version.txt"
OUTPUT_DIR = "codebase_extrator"


def ensure_output_dir():
    """Ensure that the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_next_version() -> str:
    """Get next version number (v1, v2, v3...) based on a version file."""
    if not os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "w") as f:
            f.write("1")
        return "v1"

    with open(VERSION_FILE, "r+") as f:
        version = int(f.read().strip()) + 1
        f.seek(0)
        f.write(str(version))
        f.truncate()
    return f"v{version}"


def list_files(paths: list[str]) -> list[str]:
    """Return a flat list of all file paths from given files or directories (excluding __pycache__)."""
    all_files = []
    for path in paths:
        if os.path.isfile(path):
            if "__pycache__" not in path:
                all_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                if "__pycache__" in root:
                    continue  # ignore pycache directories
                for file in files:
                    file_path = os.path.join(root, file)
                    if "__pycache__" not in file_path:
                        all_files.append(file_path)
        else:
            print(f"[WARN] Path not found: {path}")
    return all_files


def generate_filetree(files: list[str]) -> str:
    """Generate a simple text-based file tree for all files."""
    tree = ""
    for file in sorted(files):
        tree += f" - {file}\n"
    return tree


def read_files(files: list[str]) -> list[tuple[str, str]]:
    """Read all files and return a list of (filename, content)."""
    file_contents = []
    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            file_contents.append((file, content))
        except Exception as e:
            print(f"[ERROR] Could not read {file}: {e}")
    return file_contents


def write_output(version: str, code_base_name:str ,files_data: list[tuple[str, str]]):
    """Write all files into a single output file optimized for LLM reading."""
    ensure_output_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_filename = f"{code_base_name}_{version}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Build header
    header = f"### CODEBASE SNAPSHOT ({version})\n"
    header += f"### Generated at: {timestamp}\n\n"
    header += "### FILE TREE\n"
    header += generate_filetree([f for f, _ in files_data])
    header += "\n" + ("=" * 80) + "\n\n"

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(header)
        for filename, content in files_data:
            out.write(f"\n### BEGIN FILE: {filename}\n\n")
            out.write(content)
            out.write(f"\n\n### END FILE: {filename}\n")
            out.write("\n" + ("-" * 80) + "\n")

    print(f"[OK] Output written to: {output_path}")


def main():
    code_base_name = "log_extractor_and_data_calculation"
    # Example input list (edit here or receive as argument)
    input_paths = [
        "main.py",
        "config.py",
        "io_utils/",
        "processing/",
        "plotting/",
    ]
    ensure_output_dir()
    version = get_next_version()
    files = list_files(input_paths)
    files_data = read_files(files)
    write_output(version,code_base_name, files_data)


if __name__ == "__main__":
    main()