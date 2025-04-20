from enum import Enum
from enum import auto


# Idk how this works
# I stole it from https://stackoverflow.com/questions/32214614/automatically-setting-an-enum-members-value-to-its-name
class AutoNameEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


# End stolen code
