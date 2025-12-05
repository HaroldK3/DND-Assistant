import discord
from discord import app_commands, Color
from discord.ext import commands
import os
import dice_roller
from monster_manual import find_monster, mm_literals
from typing import Optional, Literal
import dotenv
from loot_generator import build_item_message, build_loot_message, parse_item_args
import json
from character_sheet import (
    init_db,
    get_character,
    insert_character,
    update_character,
    delete_character,
    import_character_from_pdf,
    set_character_owner,
    get_character_by_discord
)
from session_tracker import SessionTracker   

dotenv.load_dotenv('token.env')
token = os.environ.get('discord_bot_token')

## Create tracker instance  
tracker = SessionTracker()

## Testing with simple commands
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents = intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} is connected!')

@bot.event                  
async def on_message(message):
    if message.author != bot.user:
        tracker.log_action(1, f"{message.author.name} said: {message.content}")
    await bot.process_commands(message)

@bot.listen()               
async def on_command(ctx):
    tracker.log_action(1, f"Command started: /{ctx.command} by {ctx.author.name}")

@bot.listen()              
async def on_command_completion(ctx):
    tracker.log_action(1, f"Command completed: /{ctx.command} by {ctx.author.name}")

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author.name}!')

## @bot.command(name='help')
## async def help():
##     print("Commands: ")
##     print("/roll - rolls dice, formatted #d#(+ or -)#, being standard notation for D&D dice rolls.")

## Start actual bot logic here

## Rolling the dice -KH 
@bot.tree.command(name='roll')
async def roll_die(interaction: discord.Interaction, dice: str):
    character = get_character(interaction.user.id)

    if character:
        char_name = character["name"]
    else:
        char_name = interaction.user.display_name

    result = dice_roller.roll(dice)
    await interaction.response.send_message(f"**{char_name}** rolls: {result}")

## Search the monster manual -SM
@bot.tree.command(name='monster')
@app_commands.describe(
    name="Search by monster name.",
    category="Search by monster type.",
    size="Search by monsters size.",
    minac="Please enter an integer for minimum armor class.",
    minhp="Please enter an integer for minimum health.",
    speed="Please select a speed type.",
    align="Please select an alignment.",
    legendary="Is the monster Legendary?",
    amount="How many monsters meeting criteria to return?"
)
# All parameters are optional, so a user may use one, two, three, or all elements for their search if they'd like, allowing for more broad searches as well as more narrow searches. Also has amount variable to allow for getting a certain amount of monsters.--SM
async def search_monster(ctx, name: Optional[str], category: Optional[str], size: Optional[mm_literals.sizes], minac: Optional[int], minhp: Optional[int], speed: Optional[mm_literals.speeds], align: Optional[mm_literals.alignments], legendary: Optional[Literal["Yes", "No"]], amount: Optional[int]):
    # Issue with the display of multiple monsters taking too long, this extends the window to allow for the command to have the time it needs to operate. --SM
    await ctx.response.defer()
    results = find_monster(name, category, size, minac, minhp, speed, align, legendary, amount)
    for result in results:
        # Originally was having issues with character limit. This doubles the normal discord character limit from 2000 to 4096. --SM
        # TODO: Improve display aesthetic --SM
        # TODO: Exception handling for if message still exceeds increased character limit. --SM
        # TODO: Monster cards currently send as individual messages instead --SM
        embed = discord.Embed(
            title="Monster Manual",
            description=result,
            color=discord.Color.blue()
        )
        await ctx.followup.send(embed=embed)
    if not results:
        await ctx.response.send_message("Could not find any monsters using provided terms. Please try again.")

## Get item defined by user
@bot.command(name="item")
async def item_command(ctx, *, args: str = ""):
    rarity, item_type, magic_only = parse_item_args(args)

    result = build_item_message(
        rarity=rarity,
        item_type=item_type,
        magic_only=magic_only,
    )
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
@app_commands.describe(pdf="Upload the completed character sheet PDF")
async def importsheet(interaction: discord.Interaction, pdf: discord.Attachment):
    await interaction.response.defer()

    file_path = f"./temp_{pdf.filename}"
    await pdf.save(file_path)

    try:
        char_name = import_character_from_pdf(file_path)
        set_character_owner(char_name, str(interaction.user.id))
        msg = f"Character **{char_name}** imported and assigned to you!"
    except Exception as e:
        msg = f"Error importing sheet: {e}"

    os.remove(file_path)
    await interaction.followup.send(msg)

## Print character - KH
@bot.tree.command(name="character", description="Show your character!")
async def character(interaction: discord.Interaction):
    await interaction.response.defer()

    row = get_character_by_discord(str(interaction.user.id))
    if not row:
        await interaction.followup.send(
            "You haven't been assigned a character yet! Use /importsheet to import your character sheet first!"
        )
        return
    
    data = json.loads(row['data'])

    embed = discord.Embed(
        title=row['name'],
        description=row["class_level"] or "",
        color=0x3498db,
    )

    fields = [
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
    ]

    for label, key in fields:
        embed.add_field(name=label, value=data.get(key, "—"), inline=True)

    await interaction.followup.send(embed=embed)

# session commands -NM
@bot.command(name='session_start')
async def session_start(ctx, session_number: int, location: str, level: int):
    tracker.add_player(session_number, ctx.author.name)
    msg = tracker.start_session(session_number, location, level)
    await ctx.send(msg)

@bot.command(name='session_end')
async def session_end(ctx, session_number: int):
    recap = tracker.end_session(session_number)
    await ctx.send(recap)

@bot.command(name='xp')
async def give_xp(ctx, session_number: int, xp: int):
    tracker.add_xp(session_number, xp)
    await ctx.send(f"Added {xp} XP to session {session_number}")

@bot.command(name='add_player')
async def add_player(ctx, session_number: int, player_name: str):
    tracker.add_player(session_number, player_name)
    await ctx.send(f"{player_name} added to session {session_number}")

@bot.command(name='use_item')
async def use_item(ctx, session_number: int, *, item_name: str):
    tracker.use_consumable(session_number, item_name)
    await ctx.send(f"{ctx.author.name} used {item_name} in session {session_number}")

## running the bot
if __name__ == '__main__':
    bot.run(token)