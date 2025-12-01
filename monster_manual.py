from data.monsters import Base, Monster
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
import random
from typing import Literal
# Connects to the monstermanual DB, allows us to access it. --SM
DATABASE_URL = "sqlite:///data/monsters.db"
engine = sqla.create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = session_factory
session = Session()

class mm_literals:
    sizes = Literal['Tiny', 'Small', 'Medium', 'Large', 'Gargantuan']

    speeds = Literal["Fly", "Swim", "None"]

    alignments = Literal["neutral good","any alignment","lawful evil","chaotic evil","neutral evil","chaotic good","lawful good","unaligned","neutral","lawful neutral"]


def mm_help(align=False):
    if align is True:
        aligns = session.query(Monster).distinct.all()
        return "MONSTERMANUAL ALIGNMENTS:\n" \
               f"{aligns}"
    else:
        return "MONSTER MANUAL INSTRUCTIONS:\n" \
           "    ``monster`` - returns five random monsters.\n" \
           "    ``monster name:[name]`` - searches by the monsters name.\n" \
           "    monster type:[type]`` - searches by type of monster, returns 5 random matching values.\n" \
           "    ``monster size:[small/medium/large]`` - searches by size" \
           "    ``monster minac:[number]`` - finds 5 monsters with the stated minimum armor class.\n" \
           "    ``monster minhp:[number]`` - finds 5 monsters with the stated minimum health points.\n" \
           "    ``monster speed:[any/fly/swim/none]`` - finds 5 monsters with the stated speed type, any speed type. or no listed speed type.\n" \
           "    ``monster align:[alignment]`` - finds 5 monsters with the matching alignment type. please enter monster. please type monster help align for list of values."
# Search for a monster by its specific name. If name is null, presents a random monster from the database. --SM
def find_monster(monstername=None, monstertype=None, monstersize=None, minac=None, minhp=None, monsterspeed=None, monsteralign=None):
    results = ""
    if not any(monstername, monstertype, monstersize, minac, minhp, monsterspeed, monsteralign):
        results = session.query(Monster).where(Monster.index == random.randint(0, 761)).first()

    elif monstername:
        monstername.replace(" ", "-")
        results = session.query(Monster).where(Monster.name == monstername).first()
        if results is None:
            return f"Could not find a monster with the name '{monstername}'."
        
    elif monstertype:
        results = session.query(Monster).where(Monster.Type == monstername).first()
        if results is None:
            return f"Could not find a monster with the name '{monstername}'."
        
    elif monstersize:
        results = session.query(Monster).where(Monster.size == monstername).first()
        if results is None:
            return f"Could not find a monster with the name '{monstername}'."
    
    return results

# TODO: Add more monster manual search functions, specifically for types, legendary, etc without having to use a different command.

# def find_monster(monstertype):
#     results = ""
#     if not monstertype:
#         results = session.query(Monster).where(Monster.index == random.randint(0, 761)).first()
#     else:
#         results = session.query(Monster).where(Monster.Type == monstertype).limit(5)
#         if results is None:
#             return f"Could not find any monsters with type '{monstertype}'"
#     return results