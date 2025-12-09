import discord
from discord import app_commands, Color
from discord.ext import commands
import os
import dice_roller
from monster_manual import find_monster, display_monsters, mm_literals
from typing import Optional, Literal
import dotenv
from loot_generator import (
    parse_item_args, 
    build_inventory_message, 
    generate_item_for_user, 
    clear_inventory_for_user, 
    generate_loot_for_user
)
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
    maxac="Please enter an integer for maximum armor class.",
    minhp="Please enter an integer for minimum health.",
    maxhp="Please enter an integer for maximum health.",
    speed="Please select a speed type.",
    align="Please select an alignment.",
    legendary="Is the monster Legendary?",
    reveal="Let everyone see results?"
)
# All parameters are optional, so a user may use one, two, three, or all elements for their search if they'd like, allowing for more broad searches as well as more narrow searches. Also has amount variable to allow for getting a certain amount of monsters.--SM
async def search_monster(ctx, name: Optional[str], category: Optional[str], size: Optional[mm_literals.sizes], minac: Optional[int], maxac: Optional[int], minhp: Optional[int], maxhp: Optional[int], speed: Optional[mm_literals.speeds], align: Optional[mm_literals.alignments], legendary: Optional[Literal["Yes", "No"]], reveal: Optional[Literal["Yes","No"]]):
    # Creates a list from the find monsters method with the search terms used, if any were input.--SM
    
    results = await find_monster(name, category, size, minac, maxac, minhp, maxhp, speed, align, legendary)
   
    if not results:
        embed = discord.Embed(
            title="Could not find monsters meeting your search.", description="Please check to ensure your search values are valid, or try a different search."
        )
        await ctx.response.send_message(embed=embed, ephemeral=True)
    else:
        await display_monsters(ctx, results, tracker, reveal)     

@bot.tree.command(name="item", description="Get a random item and add it to your inventory.")
@app_commands.describe(fields="e.g. 'common weapon', 'common light armor', 'rare ring magic'")
async def item(interaction: discord.Interaction, fields: str = ""):
    rarity, item_type, magic_only = parse_item_args(fields)

    # generate & save item for user - AM
    msg = generate_item_for_user(
        discord_id=str(interaction.user.id),
        rarity=rarity,
        item_type=item_type,
        magic_only=magic_only,
    )

    embed = discord.Embed(
        title=f"{interaction.user.display_name} finds an item!",
        description=msg,
        color=0x3498db,       
    )

    await interaction.response.send_message(embed=embed)
# inventory – shows the user's items - AM
@bot.tree.command(name="inventory", description="Show your item inventory.")
async def inventory(interaction: discord.Interaction):
    msg = build_inventory_message(str(interaction.user.id))

    embed = discord.Embed(
        title=f"{interaction.user.display_name}'s Inventory",
        description=msg,
        color=0x3498db,
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="loot", description="Generate a pile of random loot and add it to your inventory.")
@app_commands.describe(chest_type="pouch (small), chest (medium), or hoard (big)")
async def loot(interaction: discord.Interaction, chest_type: str = "chest"):
    # generate loot AND save it to this user's inventory - AM
    result = generate_loot_for_user(
        discord_id=str(interaction.user.id),
        chest_type=chest_type,
        magic_only=False,  # set True for magic-only chests
    )

    # log to session tracker - NM
    tracker.record_loot(interaction.guild.id, interaction.user.name, result)

    embed = discord.Embed(
        title=f"{interaction.user.display_name} opens a {chest_type}!",
        description=result,
        color=0x3498db,
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear_inventory", description="Delete all items from your inventory.")
async def clear_inventory(interaction: discord.Interaction):
    deleted = clear_inventory_for_user(str(interaction.user.id))

    if deleted == 0:
        text = "You don't have any items in your inventory."
        color = discord.Color.red()
    else:
        text = f"Removed {deleted} item(s) from your inventory."
        color = discord.Color.orange()

    embed = discord.Embed(
        title="Inventory Cleared",
        description=text,
        color=color,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    embed, error = tracker.start_session(ctx.guild.id, session_number, location, level)
    
    if error:
        await ctx.send(f"{error}")
        return
    
    tracker.add_player(ctx.guild.id, ctx.author.name)
    await ctx.send(embed=embed)

@bot.command(name='session_end')
async def session_end(ctx, session_number: int = None):
    embed, error = tracker.end_session(ctx.guild.id)
    
    if error:
        await ctx.send(f"{error}")
        return
    
    await ctx.send(embed=embed)

@bot.command(name='session_status')
async def session_status(ctx):
    session = tracker.get_active_session(ctx.guild.id)
    
    if not session:
        await ctx.send("No active session. Start one with `/session_start`")
        return
    
    embed = discord.Embed(
        title=f"Active Session #{session['session_number']}",
        description=f"**Location:** {session['location']}\n**Level:** {session['level']}",
        color=discord.Color.green()
    )
    
    players = ", ".join(session['players']) if session['players'] else "None yet"
    embed.add_field(name="Players", value=players, inline=False)
    embed.add_field(name="Events Logged", value=str(len(session['actions_log'])), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='xp')
async def give_xp(ctx, xp: int, session_number: int = None):
    if tracker.add_xp(ctx.guild.id, xp):
        await ctx.send(f"Added **{xp} XP** to the session!")
    else:
        await ctx.send("No active session found.")

@bot.command(name='add_player')
async def add_player(ctx, player_name: str, session_number: int = None):
    if tracker.add_player(ctx.guild.id, player_name):
        await ctx.send(f"**{player_name}** added to the session!")
    else:
        await ctx.send("No active session found or player already added.")

@bot.command(name='use_item')
async def use_item(ctx, *, item_name: str):
    if tracker.use_consumable(ctx.guild.id, item_name, ctx.author.name):
        await ctx.send(f"**{ctx.author.name}** used **{item_name}**")
    else:
        await ctx.send("No active session found.")

## running the bot
if __name__ == '__main__':
    bot.run(token)
