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

def mm_clean_dict(dict_vals):
    dict_vals = {k: v for k, v in dict_vals.items() if v}
    return dict_vals

def mm_help(align=False):
    if align is True:
        aligns = session.query(Monster).distinct.all()
        return "MONSTERMANUAL ALIGNMENTS:\n" \
               f"{aligns}"
    else:
        return "MONSTER MANUAL INSTRUCTIONS:\n" \
           "    ``monster`` - returns five random monsters.\n" \
           "    ``monster name:[name]`` - searches by the monsters name.\n" \
           "    monster category:[category]`` - searches by type of monster, returns 5 random matching values.\n" \
           "    ``monster size:[small/medium/large]`` - searches by size" \
           "    ``monster minac:[number]`` - finds 5 monsters with the stated minimum armor class.\n" \
           "    ``monster minhp:[number]`` - finds 5 monsters with the stated minimum health points.\n" \
           "    ``monster speed:[any/fly/swim/none]`` - finds 5 monsters with the stated speed type, any speed type. or no listed speed type.\n" \
           "    ``monster align:[alignment]`` - finds 5 monsters with the matching alignment type. please enter monster. please type monster help align for list of values."
# Search for a monster by its specific name. If name is null, presents a random monster from the database. --SM
def find_monster(name=None, category=None, size=None, minac=None, minhp=None, speed=None, align=None, legendary=None, amnt = None):
    results = []
    if amnt is None:
        amnt = 5
    if name:
        name = name.replace(" ","-")
    if legendary == "Yes":
        legendary = 1
    elif legendary == "No":
        legendary == 0
    search_vals = {
        "name": name,
        "category" : category,
        "size" : size,
        "minac" :  minac,
        "minhp" : minhp,
        "speed" : speed,
        "align":  align,
        "legendary" : legendary
        }
    search_vals = mm_clean_dict(search_vals)
    if not search_vals:
        i = 0
        while i < amnt:
            results.append(session.query(Monster).where(Monster.index == random.randint(0, 761)).first())
            i+=1
    else:
        # TODO: Pull Random values matching the more vague search terms.--SM
        results = session.query(Monster).filter_by(**search_vals).limit(amnt).all()
    # elif name:
    #     name.replace(" ", "-")
    #     results = session.query(Monster).where(Monster.name == name).first()
    #     if results is None:
    #         return f"Could not find a monster with the name '{name}'."
        
    # elif type:
    #     results = session.query(Monster).where(Monster.Type == name).first()
    #     if results is None:
    #         return f"Could not find a monster with the name '{name}'."
        
    # elif size:
    #     results = session.query(Monster).where(Monster.size == name).first()
    #     if results is None:
    #         return f"Could not find a monster with the name '{name}'."
    
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