"""Safe token-based comment stripper for Python files."""

import os
import glob
import tokenize
import io


def strip_comments_from_file(filepath):
    """Strip all comments from a python file using the tokenize module."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    result = []
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    last_line = ""
    last_lineno = 1
    last_col = 0

    try:
        for tok in tokens:
            token_type = tok.type
            token_string = tok.string
            start_line, start_col = tok.start
            end_line, end_col = tok.end

            # Add newlines/spaces to maintain layout (somewhat)
            if start_line > last_lineno:
                result.append("\n" * (start_line - last_lineno))
                last_col = 0
            if start_col > last_col:
                result.append(" " * (start_col - last_col))

            if token_type == tokenize.COMMENT:
                # We skip the comment, but must make sure we don't break line alignment
                pass
            else:
                result.append(token_string)

            last_lineno = end_line
            last_col = end_col

    except tokenize.TokenError:
        print(f"Token error in {filepath}")
        return

    cleaned_source = "".join(result)

    # We do a basic line-by-line pass to clean up trailing whitespace left by removed comments
    clean_lines = []
    for line in cleaned_source.split("\n"):
        if line.strip() == "" and not clean_lines:
            continue
        clean_lines.append(line.rstrip())

    # Also strip double blank lines
    final_lines = []
    prev_blank = False
    for line in clean_lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        final_lines.append(line)
        prev_blank = is_blank

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines) + "\n")

    print(f"Cleaned {filepath}")


def process_repo(root_dir):
    """Process all python files in the repo."""
    patterns = [
        "*.py",
        "data/*.py",
        "server/*.py",
        "graders/*.py",
        "tasks/*.py",
        "tests/*.py",
        "agents/*.py",
    ]
    for pattern in patterns:
        for fpath in glob.glob(os.path.join(root_dir, pattern)):
            if "__pycache__" in fpath or fpath.endswith("_strip_comments.py"):
                continue
            strip_comments_from_file(fpath)


if __name__ == "__main__":
    root = r"c:\Users\Nitya\Hack\aml_monitoring_env"
    process_repo(root)
