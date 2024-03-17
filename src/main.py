import os
from io import BytesIO
from pathlib import Path
from asyncio import create_subprocess_exec, create_task, gather, run, sleep
from asyncio.subprocess import PIPE
from logging import FileHandler, StreamHandler, getLogger
from socket import gaierror
from sys import exc_info
from time import time_ns
from typing import Any, Literal, Optional

from discord import ButtonStyle, ChannelType, Client, Embed, File, Forbidden, HTTPException, Intents, Interaction, Member, Message, Object, TextChannel, Thread, VoiceClient
from discord.app_commands import CommandTree, Group, Range, describe, check
from discord.app_commands.checks import cooldown
from discord.app_commands import AppCommandError, CommandInvokeError, BotMissingPermissions, CommandOnCooldown, MissingPermissions, CheckFailure
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import setup_logging, escape_mentions
from discord.utils import get as filter_one
from discord.ui import View, Button

from yaml import safe_load as yaml_safe_load
from datetime import datetime
from random import choice, randint
from urllib.parse import urlparse
from httpx import get as http_get
from websockets import connect as ws_connect
from websockets import exceptions as WSExceptions

from deepl import Translator
from openai import AsyncOpenAI
from pydub import AudioSegment # pyright: ignore[reportMissingTypeStubs]

import utils
from database import sql_execute

os.chdir(Path(__file__).parent.parent)

setup_logging(handler=FileHandler("logfile.pylog"))
setup_logging(handler=StreamHandler())
logger = getLogger("skekbot")
info, warn, error = logger.info, logger.warning, logger.error

# Env Vars
SKEKBOT_MAIN_TOKEN = os.environ.get("SKEKBOT_MAIN_TOKEN")
SKEKBOT_DEEPL_TOKEN = os.environ.get("SKEKBOT_DEEPL_TOKEN")
SKEKBOT_OPENAI_TOKEN = os.environ.get("SKEKBOT_OPENAI_TOKEN")
SKEKBOT_CHARACTERAI_TOKEN = os.environ.get("SKEKBOT_CHARACTERAI_TOKEN")
SKEKBOT_ANNOUNCEMENT_WEBSOCKET = os.environ.get("SKEKBOT_ANNOUNCEMENT_WEBSOCKET")

if not SKEKBOT_ANNOUNCEMENT_WEBSOCKET:
    warn("SKEKBOT_ANNOUNCEMENT_WEBSOCKET is unset, announcements will not be supported!")
if not SKEKBOT_CHARACTERAI_TOKEN:
    warn("SKEKBOT_CHARACTERAI_TOKEN is unset, CharacterAI commands will not be supported!")
if not SKEKBOT_OPENAI_TOKEN:
    warn("SKEKBOT_OPENAI_TOKEN is unset, transcription will not be available!")
if not SKEKBOT_DEEPL_TOKEN:
    warn("SKEKBOT_DEEPL_TOKEN is unset, translation will not be available!")
if not SKEKBOT_MAIN_TOKEN:
    error("SKEKBOT_MAIN_TOKEN is unset, the bot cannot start!")
    exit(1)

# Config
def decode_escape(data: str) -> str:
    return bytes(data, "utf-8").replace(b"\\n", b"\x0A").decode("utf-8")

with open("config.yaml") as file:
    config: Any = yaml_safe_load(file)

OWNER_ID = int(config["OWNER_ID"])
OWNER_NAME = decode_escape(config["OWNER_NAME"])

BOT_NAME = decode_escape(config["NAME"])
ABOUT_DESCRIPTION = decode_escape(config["DESCRIPTION"])
PRIVACY_POLICY = decode_escape(config["PRIVACY_POLICY"])
SOURCE_CODE = decode_escape(config["SOURCE_CODE"])
ABOUT_COPYRIGHT = decode_escape(config["COPYRIGHT"])

WEBSOCKET_RECONNECT_INTERVAL = int(config["WEBSOCKET_RECONNECT_INTERVAL"])

# Constants
SUPPORTED_TRANSCRIPTION_AUDIO_FORMATS = ["flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"] # As per OpenAI documentation
MIN_DISCORD_MSG_LINK_LEN = 82  # Shortest possible link, 17 digit snowflakes
MAX_DISCORD_MSG_LINK_LEN = 91  # Longest possible link, 20 digit snowflakes
MAX_TRANSCRIBE_FILE_SIZE = 25  # Size in MB as per OpenAI documentation
MAX_CAI_MSG_LEN = 1024         # TODO: See the actual limit of CAI, this is arbitrary
CAI_ID_LEN = 43                # This is the exact length determined from various IDs
WS_RECONNECTION_INTERVAL = 5   # Time in seconds to wait before attempting to reconnect to the announcement WebSocket

CHARACTERAI_THREAD_VERSION = "v2"
CHARACTERAI_THREAD_NAME = f"{BOT_NAME} CharacterAI Conversation {CHARACTERAI_THREAD_VERSION}"

# Intents
intents = Intents.none()
intents.message_content = True # For What If and dad and some other things
intents.messages = True        # Same thing
intents.guilds = True          # The docs said it's a good idea to keep this enabled so...

VoiceClient.warn_nacl = False # Disables warning about PyNaCl, because we don't need voice
client = Client(intents=intents, chunk_guilds_on_startup=False)
tree = CommandTree(client)
context_menu = tree.context_menu
command = tree.command

openAiClient = None
if SKEKBOT_OPENAI_TOKEN:
    openAiClient = AsyncOpenAI(api_key=SKEKBOT_OPENAI_TOKEN)

deeplClient = None
if SKEKBOT_DEEPL_TOKEN:
    deeplClient = Translator(SKEKBOT_DEEPL_TOKEN)

class SuccessEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.blue(), title=title, type=type, url=url, description=description, timestamp=timestamp)

class FailEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.red(), title=title, type=type, url=url, description=description, timestamp=timestamp)

def testExpired(ctx: Interaction):
    return ctx.is_expired()

@client.event
async def on_error(event: str, *_):
    err = exc_info()[1]
    if isinstance(err, HTTPException):
        warn(f"{err} within {event}.")

@tree.error
async def on_app_command_error(ctx: Interaction, err: AppCommandError):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution.")
    if isinstance(err, CommandInvokeError):
        # These are often caused by a user doing something poor, such as deleting the bot's message
        return warn(f'Command {err.command.name!r} raised an exception: {err.__class__.__name__}: {err}')
    async def send(msg: str, **kwargs: Any):
        await ctx.response.send_message(msg, ephemeral=True, *kwargs)
    if isinstance(err, CommandOnCooldown):
        return await send(f"You must wait {err.retry_after:.2f}s to use this command again.")
    if isinstance(err, BotMissingPermissions):
        return await send(f"This command is unavailable because {BOT_NAME} does not have the required permissions: {", ".join(err.missing_permissions)}. Contact the server admins.")
    if isinstance(err, MissingPermissions):
        return await send(f"You do not have the required permissions to run this command: {", ".join(err.missing_permissions)}.")
    if isinstance(err, CheckFailure):
        return await send(f"You are not permitted to run this command.")

@client.event
async def on_ready():
    await tree.sync()
    info("Command tree synced!")

async def characterAI(reply: Any, character_id: str, history_id: str, message: str) -> tuple[str, str, str, str]:
    if not SKEKBOT_CHARACTERAI_TOKEN:
        return await reply(embed=FailEmbed("Command failed", "CharacterAI is not available, please contact the bot owner for more info."))
    proc = await create_subprocess_exec("node", "--no-deprecation", "./src/characterai_node", SKEKBOT_CHARACTERAI_TOKEN, character_id, history_id, message, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()
    decodedErr = err.decode("utf-8")
    if decodedErr != "":
        error(f"CharacterAI encountered errors during chat continuation: {decodedErr}")
    decoded = out.decode("utf-8")
    if decoded == "":
        return await reply("An error occured.")
    targetOutput = decoded.split("SKEKBOT OUTPUT: ", 1)[1].replace("SKEKBOT OUTPUT: ", "").splitlines()
    
    return targetOutput[0], targetOutput[1], targetOutput[2], targetOutput[3]

@client.event
async def on_message(msg: Message):
    assert client.user
    author = msg.author
    if author.id == client.user.id:
        return
    
    tasks: list[Any] = []
    
    content = msg.content
    channel = msg.channel

    # Dad
    lowContent = content.lower()
    split = lowContent.split(" ")

    # Check for "i am", because that's two words not one
    intersection_index = None
    for i, v in enumerate(split):
        if i == len(split):
            break
        if (v == "i") and (split[i+1] == "am"):
            intersection_index = (i + 1, "i a") # If "i am" is triggered, the first letter of name is cut off. I could spend time seeing why but instead I'll just do the first thing that comes to mind - shortening the trigger
            break

    if intersection_index is None:
        intersection_index = utils.first_intersection_index(split, ["i'm", "im", "i’m"])
    if intersection_index is not None:
        startIndex = len(" ".join(split[:intersection_index[0]]))
        name = content[startIndex+len(intersection_index[1])+1:]
        name = escape_mentions(name.split(",")[0].split(".")[0][:50]).title().strip() # Stop at comma / period, max 50 characters
        if name != "": # Prevents bot triggering from just saying "I am" on it's own, or by giving a blank name
            tasks.append(create_task(msg.reply(f"Hi {name}, I'm dad!")))

    
    # Messages sent in certain threads are used for AI chat
    if channel.type == ChannelType.public_thread:
        assert isinstance(channel, Thread)
        splitName = channel.name.split(" ")
        rejoinedName = " ".join(splitName[:-1])
        if rejoinedName == f"{BOT_NAME} CharacterAI":
            return await msg.reply("This thread is outdated, please create a new one.")
        elif rejoinedName == (f"{BOT_NAME} CharacterAI Conversation") and (splitName[-1] != CHARACTERAI_THREAD_VERSION):
            return await msg.reply("This thread is outdated, please create a new one.")

        if channel.name == CHARACTERAI_THREAD_NAME:
            if not SKEKBOT_CHARACTERAI_TOKEN:
                return await msg.reply(embed=FailEmbed("Command failed", "CharacterAI is not available, please contact the bot owner for more info."))
            assert isinstance(channel.parent, TextChannel)
            initMsg = (channel.starter_message) or (await channel.parent.fetch_message(channel.id))
            assert initMsg.embeds and initMsg.embeds[0] and initMsg.embeds[0].thumbnail
            url = initMsg.embeds[0].thumbnail.url
            if not url:
                return await msg.reply(embed=FailEmbed("Command failed", "An unknown error occurred."))
            data = utils.decodeImage(BytesIO(http_get(url).content))
            history_id, char_id = data[0], data[1]

            res = await characterAI(msg.reply, char_id, history_id, f"{author.name}: {content}")

            embed = SuccessEmbed("Generation completed!", res[3])
            embed.set_author(name=res[1], icon_url="https://characterai.io/i/400/static/avatars/"+res[2])
            tasks.append(create_task(msg.reply(embed=embed)))

    await gather(*tuple(tasks))

@command(description="Allows the bot owner to run various debug commands.")
@describe(command="the python code to execute. See main.py for available globals.")
@check(lambda ctx: ctx.user.id == OWNER_ID)
async def execute(ctx: Interaction, command: str):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    if ctx.user.id == OWNER_ID:
        info(f"Attempting to execute command: {command}")
        await ctx.response.defer(thinking=True)

        command = f"""
async def main_exec(_locals):
    ctx = _locals['ctx']
    returnVal = 'Set returnVal to see output.'
    try:
        {command}
    except Exception as err:
        returnVal = 'An exception was raised: '+repr(err)
        info(returnVal)
    _locals['returnVal'] = returnVal
"""
        
        _locals = locals()
        try:
            exec(command, globals(), _locals)
        except SyntaxError as err:
            errMsg = str(err)+": "+(err.text or "")
            info("SyntaxError when attempting execution: "+errMsg)
            return await ctx.followup.send(errMsg)
        await _locals["main_exec"](_locals)

        await ctx.followup.send(str(_locals["returnVal"]))

@command(description="General information about the bot.")
@cooldown(1, 30, key=lambda ctx: (ctx.guild_id, ctx.user.id))
async def about(ctx: Interaction):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    embed = SuccessEmbed(f"About {BOT_NAME}", ABOUT_DESCRIPTION)
    embed.add_field(name=ABOUT_COPYRIGHT, value="Licensed under [MPL v2.0](https://github.com/Skekdog/Skekbot/blob/main/LICENSE)")
    embed.add_field(name="Source Code", value=SOURCE_CODE)
    embed.add_field(name="Privacy", value=PRIVACY_POLICY)
    await ctx.response.send_message(embed=embed)

@command(description=f"Sets or unsets this channel to receive {BOT_NAME} announcements.")
@cooldown(1, 5, key=lambda ctx: (ctx.guild_id))
@check(lambda ctx: ctx.user.resolved_permissions.manage_channels) # type: ignore
async def set_bot_announcements(ctx: Interaction):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    assert ctx.channel_id
    res = utils.get("announcementchannels", ctx.channel_id, (False, ))
    if isinstance(res, utils.Error):
        return await ctx.response.send_message("An error occurred.", ephemeral=True)
    if res[0]:
        utils.delete("announcementchannels", ctx.channel_id)
        return await ctx.response.send_message(f"Successfully stopped this channel from receiving {BOT_NAME} announcements!")
    res = utils.update("announcementchannels", ctx.channel_id, "id", ctx.channel_id)
    if res:
        return await ctx.response.send_message("An error occurred.", ephemeral=True)
    return await ctx.response.send_message(f"Successfully set up this channel to receive {BOT_NAME} announcements!")

@command(description="Pong!")
@cooldown(2, 1)
async def ping(ctx: Interaction):
    if testExpired(ctx):
        return info(f"Command '{getattr(ctx.command, "name", "unknown")}' expired during execution, ignoring.")
    curTime = time_ns() / 1_000_000_000
    msgTime = ctx.created_at.timestamp()
    timeDiff = curTime - msgTime
    await ctx.response.send_message(embed=SuccessEmbed("🏓 Pong!").add_field(name="API", value=f"{client.ws.latency*1000:.0f}ms").add_field(name="Latency", value=f"{timeDiff*1000:.0f}ms"))

@context_menu(name="$$ Translate")
@cooldown(1, 1)
async def translate_msg(ctx: Interaction, msg: Message):
    if not deeplClient:
        return await ctx.response.send_message(embed=FailEmbed("Translation failed", "DeepL is not available, please contact the bot owner for more info."))
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    create_task(ctx.response.defer(thinking=True))

    content = msg.content
    if content == "":
        try:
            assert msg.embeds[0].description
            content = msg.embeds[0].description
        except: # Don't feel like catching the specific exceptions, too bad
            return await ctx.followup.send(embed=FailEmbed("Translation failed", "The message does not appear to have any translatable text."))
    uId = ctx.user.id
    hasEnough, alreadyUsed, available, approxCost = utils.hasEnoughCredits(uId, "translation", len(content))
    if not hasEnough:
        embed = FailEmbed("Translation failed", "You do not have enough credits.")
        embed.add_field(name="You have not been charged.", value="")
        embed.add_field(name=f"You need ${approxCost:.3f} to run this command.", value=f"You have ${(available):.3f} available.")
        return await ctx.followup.send(embed=embed)

    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")

    cost = utils.chargeUser(uId, "translation", len(content), alreadyUsed)

    result = deeplClient.translate_text(content, target_lang="EN-GB")
    embed = SuccessEmbed("Translation completed", f"`Detected Language: {result.detected_source_lang}`\n\n{result.text}") # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    embed.add_field(name=f"This translation cost ${cost:.3f}", value=f"You have ${(available-cost):.3f} available.")
    await ctx.followup.send(embed=embed) 

@command(description="Great for making a bet and immediately regretting it.")
@cooldown(2, 1)
async def coin_flip(ctx: Interaction):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    await ctx.response.send_message(utils.spoiler_pad(("Heads!" if randint(0, 1)==1 else "Tails!"), 6)) # 6 is the length of both results, future me!

class RPSButton(Button["RPSButton"]):
    def __init__(self, action: Literal["rock", "paper", "scissors"]):
        emojiCodepoint = ""
        if action == "rock":
            emojiCodepoint = "🪨"
        elif action == "paper":
            emojiCodepoint = "📰"
        elif action == "scissors":
            emojiCodepoint = f"\u2702\ufe0f" # unicode is so fun! (not)
        super().__init__(style=ButtonStyle.primary, emoji=emojiCodepoint, label=action.title())
    
    async def callback(self, interaction: Interaction):
        ctx = interaction # Annoyingly, I can't use ctx in the declaration; it must be interaction. On that note, why do I even use ctx?
        assert self.view is not None and self.label is not None
        view: RPSView = self.view # pyright: ignore[reportAssignmentType]

        await ctx.response.defer()

        async def not_party():
            await ctx.followup.send("You are not party to this game!", ephemeral=True)
        async def already_moved():
            await ctx.followup.send("You have already played your move!", ephemeral=True)

        async def check_victory():
            p1Choice, p2Choice = view.plr1Choice, view.plr2Choice
            p1Mention, p2Mention = f"<@{view.plr1}>", f"<@{view.plr2}>"
            winner = ""
            if p1Choice != "" and p2Choice != "":
                if p1Choice == "rock":
                    winner = p1Mention if p2Choice == "scissors" else p2Mention if p2Choice == "paper" else "Nobody"
                elif p1Choice == "paper":
                    winner = p1Mention if p2Choice == "rock" else p2Mention if p2Choice == "scissors" else "Nobody"
                elif p1Choice == "scissors":
                    winner = p1Mention if p2Choice == "paper" else p2Mention if p2Choice == "rock" else "Nobody"
            if winner == "":
                return
            view.stop()
            return await ctx.followup.send(f"{p1Mention} chose {p1Choice}.\n{p2Mention} chose {p2Choice}.\n\n{winner} wins!")
        
        if ctx.user.id == view.plr1:
            if view.plr1Choice == "":
                view.plr1Choice = self.label.lower()
                return await check_victory()
            else:
                return await already_moved()
        if ctx.user.id == view.plr2:
            if view.plr2Choice == "":
                view.plr2Choice = self.label.lower()
                return await check_victory()
            else:
                return await already_moved()
        else:
            return await not_party()

class RPSView(View):
    def __init__(self, plr1: int, plr2: int):
        assert client.user
        super().__init__(timeout=None)
        self.plr1 = plr1
        self.plr2 = plr2

        self.plr1Choice = ""
        self.plr2Choice = choice(["rock", "paper", "scissors"]) if (plr2 == client.user.id) else ""

        self.add_item(RPSButton("rock"))
        self.add_item(RPSButton("paper"))
        self.add_item(RPSButton("scissors"))

@command(description="The game of tactic and skill. But mostly rocks, papers, and scissors.")
@describe(versus="who to play against. Leaving this blank will default to the bot.")
async def rock_paper_scissors(ctx: Interaction, versus: Optional[Member]):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    if not versus:
        assert client.user
        return await ctx.response.send_message(f"{client.user.mention}, {ctx.user.mention} challenges you to a game of Rock, Paper, Scissors!", view=RPSView(ctx.user.id, client.user.id))
    else:
        if versus.id == ctx.user.id:
            return await ctx.response.send_message("You must be really lonely to want to verse yourself. Too bad!", ephemeral=True)
    await ctx.response.send_message(f"{versus.mention}, {ctx.user.mention} challenges you to a game of Rock, Paper, Scissors!", view=RPSView(ctx.user.id, versus.id))

@command(description="See general info on the credits system, and how many credits you have.")
@cooldown(1, 5)
async def credits(ctx: Interaction):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    uid = ctx.user.id
    embed = SuccessEmbed("Credits", f"You have ${utils.getAvailableCredits(uid):.3f} out of ${utils.getMaxCredits(uid):.3f} max.\nEach day this is replenished to ${utils.OPENAI_BUDGET:.3f}.")
    await ctx.response.send_message(embed=embed)

@command(description="$$ Transcribes an audio file or voice message.")
@describe(message_link="the full URL to the message. It must be a voice message, or have an audio attachment as it's first attachment. And it must be <25MB.",
          language="the language to translate from."
)
@cooldown(1, 5)
async def transcribe(ctx: Interaction, message_link: Range[str, MIN_DISCORD_MSG_LINK_LEN, MAX_DISCORD_MSG_LINK_LEN], language: str | None = "en") -> Any:
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    if not language:
        language = "en"
    if not openAiClient:
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "OpenAI is not available, please contact the bot owner for more info."), ephemeral=True)
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating transcription... This may take a while.")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    async def fail(reason: str, neededCredits: float | None = None, availableCredits: float | None = None):
        embed.title = "Transcription failed"
        embed.description = reason
        embed.colour = Colour.red()
        embed.add_field(name="This generation did not cost anything.", value=f"")
        if neededCredits and availableCredits:
            embed.add_field(name=f"You need ${neededCredits:.3f} to run this command.", value=f"You have ${(availableCredits):.3f} available.")
        await msgTask
        await msgTask.result().edit(embed=embed)

    link_split = urlparse(message_link).path.split("/")
    msgId, channelId = int(link_split[-1]), int(link_split[-2])

    msg = None
    try:
        msg = filter_one(client.cached_messages, id=msgId) or await client.get_partial_messageable(channelId).fetch_message(msgId)
    except Forbidden:
        return await fail("The bot does not have permission to view this message.")

    if not msg:
        return await fail("Invalid message link.")
    if (not msg.attachments) or ((msg.attachments[0].content_type or "") not in ["audio/"+type for type in SUPPORTED_TRANSCRIPTION_AUDIO_FORMATS]):
        supportedFormatsStr = ", ".join(f"{element}" for element in SUPPORTED_TRANSCRIPTION_AUDIO_FORMATS)
        return await fail(f"Message does not have a supported attachment. The message must be a voice message, or the audio is the first attachment and is one of the following formats: {supportedFormatsStr}")
    
    audio = msg.attachments[0]
    if audio.size / 1_000_000 > MAX_TRANSCRIBE_FILE_SIZE:
        return await fail(f"The audio file is too large. Maximum {MAX_TRANSCRIBE_FILE_SIZE}")
    
    data = BytesIO()
    await audio.save(data)

    data.name = "audio.ogg"

    duration = round(len(AudioSegment.from_file(data)) / 1000) # type: ignore
    hasEnoughCredits, currentSpend, available, neededCredits = utils.hasEnoughCredits(ctx.user.id, "audio", duration)
    if not hasEnoughCredits:
        return await fail("You do not have enough credits.", neededCredits, available)

    cost = utils.chargeUser(ctx.user.id, "audio", duration, currentSpend)

    data.seek(0)
    transcription = await openAiClient.audio.transcriptions.create(
        model="whisper-1",
        file=data,
        prompt="Uh... um... pfffff...",
        response_format="text",
        language=language,
    )
    data.close()

    if not transcription:
        return await fail("An unknown error occurred (1).") # Let's just start doing random error codes
    
    embed.description = str(transcription)
    embed.add_field(name=f"This generation cost ${cost:.3f}", value=f"You have ${(available-cost):.3f} available.")
    embed.title = "Transcription completed"

    await msgTask
    await msgTask.result().edit(embed=embed)

askTree = Group(name="ask", description="Chat with AI models.")

@askTree.command(name="characterai", description="Create a new chat with a CharacterAI. You can find their ID in the URL.")
@describe(character_id="can be found in the url: character.ai/chat?char=[ID IS HERE]?source=...")
@cooldown(1, 10)
async def ask_characterai(ctx: Interaction, character_id: Range[str, CAI_ID_LEN, CAI_ID_LEN]):
    if testExpired(ctx):
        return warn(f"Command {getattr(ctx.command, "name", "unknown")} expired during execution, ignoring.")
    channel = ctx.channel
    if not channel or (channel.type != ChannelType.text):
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "This command must not be run in a forum or thread."), ephemeral=True)
    await ctx.response.defer(thinking=True)

    res = await characterAI(ctx.followup.send, character_id, "None", "This is a public chat room. Separate users will be indicated by their username, followed by a colon. e.g, 'Joe: Hi!'. You must not follow this. Reply with whatever you want if you understand.")

    embed = SuccessEmbed(res[1], res[3])
    embed.set_author(name=res[1], icon_url="https://characterai.io/i/400/static/avatars/"+res[2])
    embed.set_thumbnail(url="attachment://image.png")

    msg = await ctx.followup.send(content="Thread created for conversation! Messages sent in this thread will be sent to CharacterAI for processing, along with your username. The thread name must not be changed, otherwise messages will no longer be sent.",
                                  embed=embed,
                                  file=File(utils.encodeImage((res[0], character_id)), filename="image.png"),
                                  wait=True)
    await channel.create_thread(name=CHARACTERAI_THREAD_NAME, message=Object(msg.id))

tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")

    if not SKEKBOT_ANNOUNCEMENT_WEBSOCKET:
        return await gather(clientTask)

    retryCount = 0
    while SKEKBOT_ANNOUNCEMENT_WEBSOCKET:
        try:
            async with ws_connect(SKEKBOT_ANNOUNCEMENT_WEBSOCKET) as ws:
                info("Connected to WebSocket!")
                retryCount = 0
                while True:
                    response = await ws.recv()
                    info(f"Received announcement: {response}")
                    channels = sql_execute("SELECT * FROM announcementchannels", True)
                    assert channels is not None
                    if isinstance(channels, utils.Error):
                        error(channels)
                        continue
                    embed = SuccessEmbed(f"{BOT_NAME} Announcement", description=str(response))
                    for i in channels:
                        i = i[0]
                        channel = client.get_channel(i) or (await client.fetch_channel(i))
                        try:
                            assert isinstance(channel, TextChannel)
                            await channel.send(embed=embed)
                        except Forbidden:
                            pass
        except (WSExceptions.ConnectionClosed, TimeoutError, ConnectionRefusedError):
            retryCount += 1
            if retryCount == 2:
                info(f"Announcement WebSocket closed, attempting reconnection in {WEBSOCKET_RECONNECT_INTERVAL} seconds... Further attempts will be silent.")
            elif retryCount < 2:
                info(f"Announcement WebSocket closed, attempting reconnection in {WEBSOCKET_RECONNECT_INTERVAL} seconds...")
            await sleep(WEBSOCKET_RECONNECT_INTERVAL)
        except gaierror:
            retryCount += 1
            if retryCount == 2:
                info(f"Lost connection to WebSocket, attempting reconnection in {WEBSOCKET_RECONNECT_INTERVAL} seconds... Further attempts will be silent.")
            elif retryCount < 2:
                info(f"Lost connection to WebSocket, attempting reconnection in {WEBSOCKET_RECONNECT_INTERVAL} seconds...")
            await sleep(WEBSOCKET_RECONNECT_INTERVAL)

if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        exit()