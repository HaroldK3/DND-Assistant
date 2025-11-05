import discord
from discord.ext import commands
import os
import dice_roller

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

@bot.command(name='roll')
async def roll_die(ctx, dice: str):
    result = dice_roller.roll(dice)
    await ctx.send(result)


## running the bot
if __name__ == '__main__':
    bot.run(token)