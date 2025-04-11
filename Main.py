import discord
from discord.ext import commands, tasks
import asyncio
import random
import time
import pytz
from datetime import datetime
import aiohttp  # For image search and fetching external resources
import json
import os

# Define selfbot prefix with customizable prefixes for each user or server
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", self_bot=True, intents=intents)

# Store prefix settings in a file (for persistence)
if not os.path.exists("prefixes.json"):
    with open("prefixes.json", "w") as f:
        json.dump({}, f)

with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

# Helper function to get prefix
def get_prefix(client, message):
    user_id = str(message.author.id)
    server_id = str(message.guild.id) if message.guild else None
    if server_id and server_id in prefixes:
        return prefixes[server_id]
    if user_id in prefixes:
        return prefixes[user_id]
    return "!"

# Set up the bot with a dynamic prefix
client.command_prefix = get_prefix

# Logging Command Usage
command_usage = {}

# This will run when the selfbot is ready
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await client.change_presence(activity=discord.Game(name="Selfbot is running!"))
    
# Logging commands usage
@client.event
async def on_command(ctx):
    user = ctx.author
    command = ctx.command.name
    if user.id not in command_usage:
        command_usage[user.id] = {}
    if command not in command_usage[user.id]:
        command_usage[user.id][command] = 0
    command_usage[user.id][command] += 1
    print(f"{user} used the {command} command.")
    
# Save and load prefixes from the JSON file
@client.event
async def on_message(message):
    if message.content.startswith("!setprefix"):
        new_prefix = message.content.split(" ", 1)[1]
        user_id = str(message.author.id)
        server_id = str(message.guild.id) if message.guild else None
        
        if server_id:
            prefixes[server_id] = new_prefix
        else:
            prefixes[user_id] = new_prefix
            
        with open("prefixes.json", "w") as f:
            json.dump(prefixes, f)
        
        await message.channel.send(f"Prefix changed to: {new_prefix}")
    
    await client.process_commands(message)

# Random Joke Command
@client.command()
async def joke(ctx):
    jokes = [
        "Why don’t skeletons fight each other? They don’t have the guts.",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "Why don’t some couples go to the gym? Because some relationships don’t work out.",
        "I told my computer I needed a break, and it froze."
    ]
    await ctx.send(random.choice(jokes))

# Image Search Command (using Unsplash API for random images)
@client.command()
async def image(ctx, *, query: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.unsplash.com/photos/random?query={query}&client_id=YOUR_UNSPLASH_ACCESS_KEY") as response:
            data = await response.json()
            if data:
                image_url = data[0]["urls"]["regular"]
                await ctx.send(image_url)
            else:
                await ctx.send("No images found for your query.")

# Save and retrieve quotes
quotes = []

@client.command()
async def add_quote(ctx, *, quote: str):
    quotes.append(quote)
    await ctx.send("Quote added!")

@client.command()
async def get_quote(ctx, index: int):
    try:
        quote = quotes[index]
        await ctx.send(f"Quote {index}: {quote}")
    except IndexError:
        await ctx.send("Quote not found!")

# User Info Command
@client.command()
async def userinfo(ctx, user: discord.User = None):
    user = user or ctx.author
    embed = discord.Embed(title=f"User Info: {user.name}")
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Status", value=str(user.status))
    embed.add_field(name="Joined At", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Created At", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.set_thumbnail(url=user.avatar.url)
    await ctx.send(embed=embed)

# Join and leave voice channels
@client.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel.name}!")
    else:
        await ctx.send("You need to be in a voice channel to use this command.")

@client.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I’m not in a voice channel!")

# Cooldown limit per channel to prevent command spam
cooldowns = {}

@client.command()
async def spam_limit(ctx, limit: int):
    channel_id = str(ctx.channel.id)
    cooldowns[channel_id] = limit
    await ctx.send(f"Spam limit for this channel set to {limit} messages per user per hour.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Don't respond to own messages

    channel_id = str(message.channel.id)
    if channel_id in cooldowns:
        user_id = str(message.author.id)
        current_time = time.time()
        
        if user_id not in command_usage:
            command_usage[user_id] = {"last_message_time": current_time, "message_count": 1}
        else:
            if current_time - command_usage[user_id]["last_message_time"] < 3600:
                command_usage[user_id]["message_count"] += 1
            else:
                command_usage[user_id]["message_count"] = 1

            command_usage[user_id]["last_message_time"] = current_time

            if command_usage[user_id]["message_count"] > cooldowns[channel_id]:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, you're sending too many messages too fast!")
    
    await client.process_commands(message)

# Run the bot with your user token
client.run("YOUR_USER_TOKEN", bot=False)  # Use your user token here
