import os
from pathlib import Path


class Manager:
    def __init__(self, path: Path):
        self._path = path
        self._cleared_lines, self._variables = self.readDotEnv(self._path)

    @staticmethod
    def readDotEnv(path: Path) -> tuple[list[str], set[str]]:
        cleared_lines: list[str] = []
        variables: set[str] = set()

        with open(path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line == "\n":
                    cleared_lines.append(line)
                    continue

                line = line.strip()

                split_line = line.split("=")

                variables.add(split_line[0])

                commentary_start = line.find("#")
                commentary = (
                    "    " + line[commentary_start:] if commentary_start != -1 else ""
                )

                final_line = split_line[0] + "=" + commentary

                cleared_lines.append(final_line)

        return cleared_lines, variables

    def generateClearedDotEnv(self, path: Path):
        with open(path, "w") as file:
            for line in self._cleared_lines:
                file.write(line)
                if line != "\n":
                    file.write("\n")

    def isDotEnvFull(self, other_dotenv: Path) -> tuple[bool, set[str]]:
        """returns the status and the missing values set"""

        _, other_dotenv_variables = self.readDotEnv(other_dotenv)

        missing_variables_in_dotenv = set()

        for other_dotenv_variable in other_dotenv_variables:
            if other_dotenv_variable not in self._variables:
                missing_variables_in_dotenv.add(other_dotenv_variable)

        if missing_variables_in_dotenv:
            return (
                False,
                missing_variables_in_dotenv,
            )  # False because dotenv is not full
        else:
            return True, missing_variables_in_dotenv


if __name__ == "__main__":
    # os.chdir("/")
    print(os.listdir("./"))
    print(os.getcwd())

    # manager = Manager(Path(".env"))
    # manager.generateClearedDotEnv(Path("example.env"))
    # print(manager.isDotEnvFull(Path("example.env")))

    os.system("mkdir example")

    skip_filenames = ["old.env", "old_example.env", "run_me_after_changing_env.py"]
    for filename in os.listdir("./"):
        if filename in skip_filenames:
            continue
        if "example_" in filename:
            continue
        if not (".env" in filename):
            continue

        manager = Manager(Path(filename))
        manager.generateClearedDotEnv(Path("example/" + filename))
