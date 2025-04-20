from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from . import *

if __name__ == "__main__":
    # imports are placed in this IF because they have to be initialized by python but not fastapi
    from .engine import engine, Base

    # Base.metadata.create_all(engine)

    from . import *
