import discord
from discord.ext import commands
import os
import dice_roller
from monster_manual import find_monster
from typing import Optional
import dotenv

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

## running the bot
if __name__ == '__main__':
    bot.run(token)