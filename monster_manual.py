from data.monsters import Base, Monster
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
import random
# Connects to the monstermanual DB, allows us to access it. --SM
DATABASE_URL = "sqlite:///data/monsters.db"
engine = sqla.create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = session_factory
session = Session()

# Search for a monster by its specific name. If name is null, presents a random monster from the database. --SM
def find_monster(monstername):
    results = ""
    if not monstername:
        results = session.query(Monster).where(Monster.index == random.randint(0, 761)).first()
    else:
        results = session.query(Monster).where(Monster.name == monstername).first()
        if results is None:
            return f"Could not find a monster with the name {monstername}."
    return  results

# TODO: Add more monster manual search functions, specifically for types, legendary, etc without having to use a different command.