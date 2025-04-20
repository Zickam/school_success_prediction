
from . import user, school

from ..engine import Base, engine, getSession

# Base.metadata.create_all(engine)

# # Step 5: Create a session
# session = getSession()
#
# # Step 6: Add new data
# new_user = User(name='Alice')
# session.add(new_user)
# session.commit()
#
# # Step 7: Query data
# users = session.query(User).all()