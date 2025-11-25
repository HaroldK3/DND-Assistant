import discord
from discord.ext import commands
import os
import dice_roller
from monster_manual import find_monster
from typing import Optional
import dotenv
from loot_generator import build_item_message, build_loot_message

dotenv.load_dotenv()
token = os.environ.get('discord_bot_token')


## Testing with simple commands
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents = intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is connected!')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author.name}!')

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

## running the bot
if __name__ == '__main__':
    bot.run(token)
