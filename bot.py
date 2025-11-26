import discord
from discord import app_commands
from discord.ext import commands
import os
import dice_roller
from monster_manual import find_monster
from typing import Optional
import dotenv
from loot_generator import build_item_message, build_loot_message
import json
from character_sheet import (
    init_db,
    get_character,
    insert_character,
    update_character,
    delete_character,
    import_character_from_pdf
)

dotenv.load_dotenv()
token = os.getenv('discord_bot_token')


## Testing with simple commands
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents = intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} is connected!')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author.name}!')

## @bot.command(name='help')
## async def help():
##     print("Commands: ")
##     print("/roll - rolls dice, formatted #d#(+ or -)#, being standard notation for D&D dice rolls.")

## Start actual bot logic here

## Rolling the dice -KH 
@bot.command(name='roll')
async def roll_die(ctx, dice: str):
    result = dice_roller.roll(dice)
    await ctx.send(result)

## Search the monster manual -SM
@bot.command(name='monster')
# monstername is set to optional so that if the monstername is not provided, it can provide a random monster from the DB. --SM
async def search_monster(ctx, monstername: Optional[str]):
    result = find_monster(monstername)
    await ctx.send(result)

## Get item defined by user
@bot.command(name="item")
async def item_command(ctx, rarity: str = "random", item_type: str = "any", magic_only: str = "no"):
    result = build_item_message(rarity=rarity, item_type=item_type, magic_only=magic_only)
    await ctx.send(result)

## Loot a chest for a random amount of random loot
@bot.command(name="loot")
async def loot_command(ctx, chest_type: str = "chest"):
    """Generate a pile of loot."""
    result = build_loot_message(chest_type=chest_type)
    await ctx.send(result)


## Character Sheet stuff -KH
def format_character(row):
    data = json.loads(row["data"])
    embed = discord.Embed(
        title=f"{row['name']}",
        description=row["class_level"] or "No class level.",
        color=0x3498db,
    )

    fields_to_show = [
        ("Race", "Race "),
        ("Background", "Background"),
        ("STR", "STR"),
        ("DEX", "DEX"),
        ("CON", "CON"),
        ("INT", "INT"),
        ("WIS", "WIS"),
        ("CHA", "CHA"),
        ("HP Max", "HPMax"),
        ("HP Current", "HPCurrent"),
        ("AC", "AC"),
        ("Speed", "Speed"),
        ("Passive Perception", "Passive"),
    ]

    for title, key in fields_to_show:
        embed.add_field(name="title", value=data.get(key, "—"), inline=True)

    embed.set_footer(text="D&D Character Sheet")

    return embed

@bot.tree.command(name="importsheet", description="Import a PDF character sheet")
@app_commands.describe(pdf="Upload the completed PDF")
async def importsheet(interaction: discord.Interaction, pdf: discord.Attachment):
    await interaction.response.defer()

    file_path = f"./temp_{pdf.filename}"
    await pdf.save(file_path)

    try:
        char_name = import_character_from_pdf(file_path)
        msg = f"Character **{char_name}** imported!"
    except Exception as e:
        msg = f"Error importing sheet: {e}"

    os.remove(file_path)
    await interaction.followup.send(msg)




## running the bot
if __name__ == '__main__':
    bot.run(token)
