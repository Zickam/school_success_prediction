from enum import Enum
from enum import auto


class AutoNameEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name
