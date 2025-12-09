from data.monsters import Base, Monster
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
import random
from typing import Literal
import discord


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
    embed.add_field(name="**Stats**", value="", inline=False)
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
    def __init__(self, monsters:list[Monster], ctx, tracker):
        super().__init__()
        self.current_page = 0
        self.num_pages = len(monsters)
        self.monsters = monsters
        self.ctx = ctx
        self.tracker = tracker

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def prev(self, interaction, button):
        if self.current_page == 0:
            button.disabled = True
        else:
            self.current_page -= 1
        await interaction.response.edit_message(embed=mm_build_embed(self.monsters[self.current_page]))

    @discord.ui.button(label="Log for Session", style=discord.ButtonStyle.success)
    async def track_monster(self, interaction, button):
        active_session = self.tracker.get_active_session(self.ctx.guild.id)
        await interaction.response.defer()
        monster_to_track = [self.monsters[self.current_page]]
        if active_session:
            self.tracker.record_monster(self.ctx.guild.id, self.ctx.user.name, monster_to_track)
            await interaction.followup.send(f"Successfully tracked {self.monsters[self.current_page].name} to session log.", ephemeral=True)
        else:
            await interaction.followup.send(f"Unable to track monster: No session is currently active.", ephemeral=True)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        if self.current_page == len(self.monsters) - 1:
            button.disabled = True
        else:
            self.current_page += 1
        await interaction.response.edit_message(embed=mm_build_embed(self.monsters[self.current_page]))
        
    
## Acceptable values for search input that depends on a strict set of values.--SM
class mm_literals:
    valid_params = ["name", "category", "size", "minac", "maxac", "minhp", "maxhp", "speed", "align", "legendary"]

    sizes = Literal['Tiny', 'Small', 'Medium', 'Large', 'Gargantuan']

    speeds = Literal["fly", "swim", "None"]

    alignments = Literal["neutral good","any alignment","lawful evil","chaotic evil","neutral evil","chaotic good","lawful good","unaligned","neutral","lawful neutral"]

# Removes null and empty values from the user response. i.e /monster category:undead provides only the search term undead.--SM
async def clean_dict(dict_vals):
    dict_vals = {k: v for k, v in dict_vals.items() if v}
    return dict_vals

# Resource used: https://www.w3schools.com/python/python_lists_comprehension.asp
def filter_by_ac(minac, maxac, monsters):
    if maxac is None:
        filtered_monsters = [monster for monster in monsters if monster.AC >= minac]
    elif minac is None:
        filtered_monsters = [monster for monster in monsters if monster.AC <= maxac]
    else:
        filtered_monsters = [monster for monster in monsters if monster.AC >= minac and monster.AC <= maxac]
    return filtered_monsters

def filter_by_hp(minhp, maxhp, monsters):
    if maxhp is None:
        filtered_monsters = [monster for monster in monsters if monster.HP >= minhp]
    elif minhp is None:
        filtered_monsters = [monster for monster in monsters if monster.HP <= maxhp]
    else:
        filtered_monsters = [monster for monster in monsters if monster.HP >= minhp and monster.HP <= maxhp]
    return filtered_monsters

# Search for a monster by varying search terms. If name is null, presents a random monster from the database. --SM
async def find_monster(name=None, category=None, size=None, minac=None, maxac=None, minhp=None, maxhp=None, speed=None, align=None, legendary=None):
    results = []
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
        "speed" : speed,
        "alignment":  align,
        "legendary" : legendary
        }
    search_vals = await clean_dict(search_vals)
    if not search_vals:
        results = session.query(Monster).all()
    else:
        # TODO: Pull Random values matching the more vague search terms.--SM
        results = session.query(Monster).filter_by(**search_vals).all()
    if minac or maxac:
        results = filter_by_ac(minac, maxac, results)
    if minhp or maxhp:
        results = filter_by_hp(minhp, maxhp, results)
    return results


# Creates the menu for the monster display with the embed, buttons. Creates the first monster from the results of the search allowing for a starting point of the menu. Tracker is passed from bot.py to allow us to use the session_tracker's record_monster function.--SM
async def display_monsters(ctx, monsters: list[Monster], tracker, reveal):
    view = menu_nav(monsters, ctx,tracker)
    first_monster = mm_build_embed(monsters[0])
    if reveal == "Yes":
        await ctx.response.send_message(embed=first_monster, view=view)
    else:
        await ctx.response.send_message(embed=first_monster, view=view, ephemeral=True)

