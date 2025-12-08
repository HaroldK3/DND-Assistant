from data.monsters import Base, Monster
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
import random
from typing import Literal
import discord

# TODO: General error handling.
# TODO: Combat encounters?

# Connects to the monstermanual DB, allows us to access it. --SM
DATABASE_URL = "sqlite:///data/monsters.db"
engine = sqla.create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = session_factory
session = Session()

# Dedicated method to build the embed for the monster. I made it it's own method for easier maintenance, as well as attempting to make things look cleaner by removing such a large block of code from another method --SM
def mm_build_embed(monster: Monster):
    embed = discord.Embed(
            title="Monster Manual",
            description=monster.name,
            color=discord.Color.blue()
        )
    embed.add_field(name="Category:", value=monster.category, inline=True)
    embed.add_field(name="Size", value=monster.size, inline=True)
    embed.add_field(name="Health Points", value=monster.HP, inline=True)
    embed.add_field(name="Challenge Rating", value=monster.CR, inline=True)
    embed.add_field(name="Armor Class", value=monster.AC, inline=True)
    embed.add_field(name="Speed", value=monster.speed, inline=True)
    embed.add_field(name="Alignment", value=monster.alignment, inline=True)
    embed.add_field(name="Legendary", value=monster.legendary, inline=True)
    embed.add_field(name="Source", value=monster.source, inline=True)
    embed.add_field(name="Stats", value="**Stats**", inline=False)
    embed.add_field(name="STR", value=monster.strength, inline=True)
    embed.add_field(name="DEX", value=monster.dexterity, inline=True)
    embed.add_field(name="CON", value=monster.constitution, inline=True)
    embed.add_field(name="INT", value=monster.intelligence, inline=True)
    embed.add_field(name="WIS", value=monster.wisdom, inline=True)
    embed.add_field(name="CHA", value=monster.charisma, inline=True)
    embed.add_field(name="View Page:", value=monster.url, inline=False)
    
    return embed
## I was having an issue of multiple monsters printing individual messages. This allows the end user to navigate through a menu of monsters meeting their described search instead of having to use individual embeds, meet the needs of character requirements, etc.--SM

"""Credit goes to these resources for helping me to understand better:
How to Create a Button Menu Easy (by: Civo): https://www.youtube.com/watch?v=82d9s8D6XE4
All you need to know about Buttons in Discord.py & Pycord (By code with Swastik): https://www.youtube.com/watch?v=kNUuYEWGOxA
PyCord Guide - Buttons: https://guide.pycord.dev/interactions/ui-components/buttons
"""
class menu_nav(discord.ui.View):
    def __init__(self, monsters:list[Monster]):
        super().__init__()
        self.current_page = 0
        self.num_pages = len(monsters)
        self.monsters = monsters

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def prev(self, interaction, button):
        if self.current_page == 0:
            button.disabled = True
        else:
            self.current_page -= 1
        await interaction.response.edit_message(embed=mm_build_embed(self.monsters[self.current_page]))
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        if self.current_page == len(self.monsters) - 1:
            button.disabled = True
        else:
            self.current_page += 1
        await interaction.response.edit_message(embed=mm_build_embed(self.monsters[self.current_page]))
        
    
## Acceptable values for search input that depends on a strict set of values.--SM
class mm_literals:
    sizes = Literal['Tiny', 'Small', 'Medium', 'Large', 'Gargantuan']

    speeds = Literal["Fly", "Swim", "None"]

    alignments = Literal["neutral good","any alignment","lawful evil","chaotic evil","neutral evil","chaotic good","lawful good","unaligned","neutral","lawful neutral"]

# Removes null and empty values from the user response. i.e /monster category:undead provides only the search term undead.--SM
async def clean_dict(dict_vals):
    dict_vals = {k: v for k, v in dict_vals.items() if v}
    return dict_vals

# Unsure if this will be implemented at the end.--SM
async def mm_help(align=False):
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
# Search for a monster by varying search terms. If name is null, presents a random monster from the database. --SM
# TODO: Check ALL search terms. For sure, fix minhp.
async def find_monster(name=None, category=None, size=None, minac=None, minhp=None, speed=None, align=None, legendary=None, amnt = None):
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
        # These two lines may be the cause for headache with minhp not working. Not a variable in Monster, so likely falling flat when used.
        "minac" :  minac,
        "minhp" : minhp,
        "speed" : speed,
        "align":  align,
        "legendary" : legendary
        }
    search_vals = await clean_dict(search_vals)
    # TODO: Fix to make list entire monster manual, instead of a random one. No need to randomize as it is easier to sift through with menu.--SM
    if not search_vals:
        i = 0
        while i < amnt:
            results.append(session.query(Monster).where(Monster.current_page == random.randint(0, 761)).first())
            i+=1
    else:
        # TODO: Pull Random values matching the more vague search terms.--SM
        results = session.query(Monster).filter_by(**search_vals).limit(amnt).all()
    return results


# Creates the menu for the monster display with the embed, buttons. Creates the first monster from the results of the search allowing for a starting point of the menu.--SM
async def display_monsters(ctx, monsters: list[Monster]):
    view = menu_nav(monsters)
    first_monster = mm_build_embed(monsters[0])
    await ctx.response.send_message(embed=first_monster, view=view)

