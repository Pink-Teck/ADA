#discord
import discord
from discord.ext import commands
from discord import app_commands

#server script
import server

#api script
import game_api

#supporting libs
import asyncio
from dotenv import load_dotenv
import os


#Config Loading--------------------------------------
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("Discord Token is None.")

GUILD = discord.Object(id=int(os.getenv('GUILD_ID')))
if not GUILD:
    raise ValueError("Guild ID is None.")

BOT_CHANNEL = os.getenv('BOT_CHANNEL')
if not BOT_CHANNEL:
    raise ValueError("Bot Channel value is None.")

ec2_client = server.get_ec2_client()

#Client Setup---------------------------------------
class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        try:
            guild = discord.Object(id=GUILD)
            synced = await self.tree.sync(guild=guild)
            print(f"synced {len(synced)} commands to guild {guild.id}")
        except Exception as e:
            print(f"Error syncing commands: {e}")
            
    async def on_message(self, message):
        print(f'[msg][{message.author}]: {message.content}')

#Intents / Permissions
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

#Channel Scope---------------------------------------
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

#==Commands============================================

#Strings -
endline = "\n----------------------------------------"
loading = "\n :hourglass:"

#/hello - for testing
@client.tree.command(name="hello", description="say hello", guild=GUILD)
async def sayHello(interaction: discord.Interaction):
    await interaction.response.send_message("hello")

#auto stop---------------------------------------
async def autoStop():
    
    channel = client.get_channel(int(BOT_CHANNEL))

    #Var
    wait_time = 3
    stop_counter = wait_time
    no_response_counter = 0
    failed_stop_counter = 0
    stop = False

    #Give players a few mins to connect before checking for empty session
    await asyncio.sleep(120)

    while not stop:
        try:
            result, response = await asyncio.to_thread(game_api.main)

            #How to handle repeated fails
            if not result:
                no_response_counter += 1
                if no_response_counter == 5:
                    await channel.send(":x: auto-shutdown monitoring has been offline for 5 mins :x:", )
                    await channel.send("<@163035737577619457> Autoshutdown may be broken. Please fix.")

            #But assuming everything is working..
            else:
                no_response_counter = 0
                if response > 0:
                    stop_counter = wait_time
                else:
                    stop_counter -= 1
                    await channel.send(f"DEBUG: stop_counter = {stop_counter}")

                    #Stop counter hits 0 (10 mins) and sends stop command
                    if stop_counter <= 0:
                        result, message = await asyncio.to_thread(server.cmd_stop, ec2_client)
                        if result:
                            failed_stop_counter = 0
                            await channel.send("**== :red_circle: SERVER STOPPED :red_circle: ==**")
                            stop = True #Stop this loop
                        else:
                            #wait for 5 failed stops before suppressing + notifying
                            failed_stop_counter += 1
                            if failed_stop_counter < 5:
                                await channel.send("**== :x: SHUTDOWN FAILED :x: ==**")
                            elif failed_stop_counter == 5:
                                await channel.send("Supressing further shutdown failure messages.")

        except Exception as exc:
            print(f"autostop: unexpected error: {exc}")

        await asyncio.sleep(60)


#/start------------------------------------------
@client.tree.command(name="start", description="start the server", guild=GUILD)
async def startServer(interaction: discord.Interaction):
    current_msg = ""

    #add title line to message + send
    next_line = "== :blue_circle: STARTING AWS SERVER :blue_circle: =="
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
        current_msg = "**== :orange_circle: AWS EC2 INSTANCE ONLINE :orange_circle: ==**"
        await interaction.edit_original_response(content=f"{current_msg}{loading}")

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
        return

    #Start Satisfactory Server
    next_line = "\n Spinning up the Satisfactory Game server..."
    current_msg += next_line
    await interaction.edit_original_response(content=f"{current_msg}{loading}")

    connection_checks = 24
    connection = False
    while not connection:
        result, message = await asyncio.to_thread(game_api.test_connection)
        if result:
            current_msg = "**== :green_circle: SERVER ONLINE :green_circle: ==**"
            await interaction.edit_original_response(content=f"{current_msg}{endline}")
            connection = True
        else:
            connection_checks -= 1
            if connection_checks < 1:
                current_msg = "**== :x: SATISFACTORY SERVER FAILED :x: ==**"
                next_line = f"\n- Satisfactory server failed to be online after 2 minutes\n- Server may still be launching, check agian in a minute\n- message: {message}"
                await interaction.edit_original_response(content=f"{current_msg + next_line}{endline}")
                return
            await asyncio.sleep(5)

    stop_command = autoStop
    try:
        asyncio.create_task(stop_command())
    except:
        raise Exception("Error in autoStop")


#/stop (DEPRECATION IN PROGRESS)-------------------------------------

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

#/status-----------------------------------------
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

client.run(token)