import os
import re


def remove_comments_from_code(code):
    code = re.sub(r"(\"\"\".*?\"\"\")|(\'\'\'.*?\'\'\')", "", code, flags=re.DOTALL)

    cleaned_lines = []
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        new_line = ""
        i = 0
        while i < len(line):
            if line[i] in ('"', "'"):
                quote = line[i]
                new_line += quote
                i += 1
                while i < len(line):
                    new_line += line[i]
                    if line[i] == quote and line[i - 1] != "\\":
                        i += 1
                        break
                    i += 1
            elif line[i] == "#":
                break
            else:
                new_line += line[i]
                i += 1
        cleaned_lines.append(new_line.rstrip())
    return "\n".join(cleaned_lines)


for root, dirs, files in os.walk("."):
    for filename in files:
        if filename.endswith(".py"):
            path = os.path.join(root, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    original_code = file.read()
                cleaned_code = remove_comments_from_code(original_code)
                with open(path, "w", encoding="utf-8") as file:
                    file.write(cleaned_code)
                print(f"Cleaned: {path}")
            except Exception as e:
                print(f"Failed to process {path}: {e}")
