#discord
import discord
from discord.ext import commands
from discord import app_commands

#server script
import server

#supporting libs
import asyncio
from dotenv import load_dotenv
import os
import logging


#Config Loading
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
GUILD = discord.Object(id=int(os.getenv('GUILD_ID')))
BOT_CHANNEL = os.getenv('BOT_CHANNEL')
ec2_client = server.get_ec2_client()

#Client Setup
class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        try:
            guild = discord.Object(id=1525936438342844508)
            synced = await self.tree.sync(guild=guild)
            print(f"synced {len(synced)} commands to guild {guild.id}")
        except Exception as e:
            print(f"Error syncing commands: {e}")
            
    async def on_message(self, message):
        print(f'[msg][{message.author}]: {message.content}')


intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

#Channel Scope
async def interaction_check(interaction: discord.Interaction) -> bool:
    if interaction.channel_id != int(BOT_CHANNEL):
        await interaction.response.send_message(
            "This command can only be used from #satisfactory-server",
            ephemeral=True
        )
        return False
    return True

client.tree.interaction_check = interaction_check

#==Logging== ->Future goal
#handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

#==Commands==

#Strings
endline = "\n----------------------------------------"
loading = "\n :hourglass:"

#/hello - for testing
@client.tree.command(name="hello", description="say hello", guild=GUILD)
async def sayHello(interaction: discord.Interaction):
    await interaction.response.send_message("hello")

#/start
@client.tree.command(name="start", description="start the server", guild=GUILD)
async def startServer(interaction: discord.Interaction):
    current_msg = ""

    #add title line to message + send
    next_line = "== :rocket: STARTING SERVER :rocket: =="
    current_msg += next_line
    await interaction.response.send_message(f"{current_msg}{loading}")

    #add greeting line to message + send
    next_line = f"\n Welcome back EMPLOYEE:{interaction.user.display_name}"
    current_msg += next_line
    await interaction.edit_original_response(content=f"{current_msg}{loading}")

    #add flavour + send
    next_line = "\n Turning the lights on..."
    current_msg += next_line
    await interaction.edit_original_response(content=f"{current_msg}{loading}")

    #send start command, store result
    result, message = await asyncio.to_thread(server.cmd_start, ec2_client)

    #if start successful
    if result:
        current_msg = "**== :green_circle: EC2 INSTANCE ONLINE :green_circle: ==**"
        await interaction.edit_original_response(content=f"{current_msg}")

    #if start unsuccussful
    else:
        #update to failed status
        current_msg = "**== :x: EC2 INSTANCE FAILED :x: ==**"
        await interaction.edit_original_response(content=f"{current_msg}{loading}")

        #fetch state
        state, _ = await asyncio.to_thread(server.cmd_status, ec2_client)

        next_line = f"\n| State: **{state}** | Error: {message} |"
        current_msg += next_line
        await interaction.edit_original_response(content=f"{current_msg}{endline}")


#/stop
@client.tree.command(name="stop", description="stop the server", guild=GUILD) 
async def stopServer(interaction: discord.Interaction):
    current_msg = ""

    #add title line + send
    next_line = "== :stop_sign: STOPPING SERVER :stop_sign: =="
    current_msg += next_line
    await interaction.response.send_message(f"{current_msg}{loading}")

    #add flavor
    next_line = "\nThis may take a minute..."
    current_msg += next_line
    await interaction.edit_original_response(content=f"{current_msg}{loading}")

    #send stop command + store result
    result, message = await asyncio.to_thread(server.cmd_stop, ec2_client)

    #if shutdown success
    if result:
        current_msg = "**== :red_circle: SERVER STOPPED :red_circle: ==**"
        await interaction.edit_original_response(content=f"{current_msg}")

    #if shutdown failed
    else:
        current_msg = "**== :x: SHUTDOWN FAILED :x: ==**"
        await interaction.edit_original_response(content=f"{current_msg}{loading}")

        #grab state and store it
        state, _ = await asyncio.to_thread(server.cmd_status, ec2_client)

        #add info to message and send
        next_line = f"| State: **{state}** | Error: {message} |"
        current_msg += next_line
        await interaction.edit_original_response(content=f"{current_msg}{endline}")

#/status
@client.tree.command(name="status", description="instance status", guild=GUILD)
async def statusServer(interaction: discord.Interaction):
    current_msg = ""

    #add title message to current + send
    next_line = "** :bar_chart: STATUS REPORT :bar_chart: **"
    current_msg += next_line
    await interaction.response.send_message(f"{current_msg}{loading}")

    #grab ec2 instance state
    state, publicIP = await asyncio.to_thread(server.cmd_status, ec2_client)

    #add result to current + send
    next_line = f"\n | State: **{state}** | PublicIP: **{publicIP}** | "
    current_msg += next_line
    await interaction.edit_original_response(content=f"{current_msg}{endline}")

#polling

client.run(token)