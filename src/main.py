import os
from io import BytesIO
from pathlib import Path
from asyncio import create_task, gather, run, CancelledError, InvalidStateError
from logging import FileHandler, StreamHandler, getLogger
from typing import Any

from discord import ChannelType, Client, Embed, File, Intents, Interaction, Object
from discord import VoiceClient
from discord.app_commands import CommandTree, Group, Range, describe
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import setup_logging
from discord.utils import get as filterOne

from characterai import PyAsyncCAI # pyright: ignore[reportMissingTypeStubs]
from datetime import datetime
from random import randint
from urllib.parse import urlparse
from httpx import get

import utils
from database import sql_execute # pyright: ignore[reportUnusedImport] | Can be used in /execute

os.chdir(Path(__file__).parent.parent)

setup_logging(handler=FileHandler("logfile.pylog"))
setup_logging(handler=StreamHandler())
logger = getLogger("skekbot")
info, warn, error = logger.info, logger.warning, logger.error

# Constants

SUPPORTED_TRANSCRIPTION_AUDIO_FORMATS = ["flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"] # As per OpenAI documentation
OWNER_ID = 534828861586800676  # That's me
MIN_DISCORD_MSG_LINK_LEN = 82  # Shortest possible link, 17 digit snowflakes
MAX_DISCORD_MSG_LINK_LEN = 91 # Longest possible link, 20 digit snowflakes
MAX_TRANSCRIBE_FILE_SIZE = 25  # Size in MB as per OpenAI documentation
MAX_CHATGPT_MSG_LEN = 2048     # Half of max output (which is both input and output combined)
MAX_CAI_MSG_LEN = 1024         # TODO: See the actual limit of CAI, this is arbitrary
CAI_ID_LEN = 43                # Exact length determined from various IDs
BOT_INVITE = "https://discord.com/api/oauth2/authorize?client_id=1054474727642628136&permissions=311385508864&scope=bot"

# Intents
intents = Intents.none()
intents.message_content = True # For What If and dad and some other things
intents.messages = True        # Same thing
intents.guilds = True          # The docs said it's a good idea to keep this enabled so...

VoiceClient.warn_nacl = False # Disables warning about PyNaCl, because we don't need voice
client = Client(intents=intents, chunk_guilds_on_startup=False)
tree = CommandTree(client)
command = tree.command

CAIClient = PyAsyncCAI(os.environ["SKEKBOT_CHARACTERAI_TOKEN"])

class SuccessEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.blue(), title=title, type=type, url=url, description=description, timestamp=timestamp)

class FailEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.red(), title=title, type=type, url=url, description=description, timestamp=timestamp)

@client.event
async def on_ready():
    await tree.sync()
    info("Command tree synced!")

@command(description="Allows the bot owner to run various debug commands.")
@describe(command="the python code to execute. See main.py for available globals.")
async def execute(ctx: Interaction, command: str):
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
async def about(ctx: Interaction):
    embed = SuccessEmbed("About Skekbot", "Skekbot is a mostly-for-fun Discord bot, developed by... Skekdog, using the [discord.py](https://github.com/Rapptz/discord.py) library.\nClick [here](https://discord.com/api/oauth2/authorize?client_id=1054474727642628136&permissions=311385508864&scope=bot) to invite Skekbot to your server.\n\nPrivacy: Data is stored about your expenses incurred for [OpenAI](https://openai.com/). For processing, your prompts are sent to [OpenAI](https://openai.com/) or [Character.AI](https://beta.character.ai/).")
    embed.add_field(name="Copyright Skekdog © 2024", value="Licensed under [MPL v2.0](https://github.com/Skekdog/Skekbot/blob/main/LICENSE)")
    embed.add_field(name="Source Code", value="[GitHub](https://www.github.com/Skekdog/Skekbot)")
    await ctx.response.send_message(embed=embed)

@command(description="Great for making a bet and immediately regretting it.")
async def coin_flip(ctx: Interaction):
    await ctx.response.send_message("Heads!" if randint(0,1)==1 else "Tails!")

@command(description="$$ Transcribes an audio file or voice message.")
@describe(message_link="the full URL to the message. It must be a voice message, or have an audio attachment as it's first attachment. And it must be <25MB.")
async def transcribe(ctx: Interaction, message_link: Range[str, MIN_DISCORD_MSG_LINK_LEN, MAX_DISCORD_MSG_LINK_LEN]):
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating transcription... This may take a while.")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    async def fail(reason: str):
        embed.title = "Transcription failed"
        embed.description = reason
        embed.colour = Colour.red()
        await msgTask
        await msgTask.result().edit(embed=embed)

    link_split = urlparse(message_link).path.split("/")
    msgId, channelId = int(link_split[-1]), int(link_split[-2])

    msg = filterOne(client.cached_messages, id=msgId) or await client.get_partial_messageable(channelId).fetch_message(msgId)

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
    transcription = await utils.transcribe(ctx.user.id, data)

    if not transcription:
        return await fail("You do not have enough credits.")
    
    embed.description = transcription
    embed.title = "Transcription completed"

    await msgTask
    await msgTask.result().edit(embed=embed)

askTree = Group(name="ask", description="Chat with AI models.")
@askTree.command(name="gpt", description="$$ Chat with OpenAI's ChatGPT 3.5.")
@describe(prompt=f"the prompt to provide, up to {MAX_CHATGPT_MSG_LEN} characters.")
async def ask_gpt(ctx: Interaction, prompt: Range[str, None, MAX_CHATGPT_MSG_LEN]):
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating response...")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    async def update(msg: str, failed: bool):
        try:
            if failed:
                await msgTask
                return await msgTask.result().edit(embed=FailEmbed("Generation failed", msg))
            embed.description = msg
            await msgTask.result().edit(embed=embed)
        except (CancelledError, InvalidStateError): pass
    
    await utils.chatGPT(ctx.user.id, prompt, update) # type: ignore # TODO: This is nicht gut

CAITree = Group(name="character_ai", description="Chat with character.ai models.")
@CAITree.command(name="create", description="Create a new chat with a Character. You can find their ID in the URL.")
@describe(character_id="can be found in the url: character.ai/chat?char=[ID IS HERE]?source=...")
async def ask_character_ai_create(ctx: Interaction, character_id: Range[str, CAI_ID_LEN, CAI_ID_LEN]):
    channel = ctx.channel
    if not channel or (channel.type != ChannelType.text):
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "This command must not be run in a forum or thread."))
    await ctx.response.defer(thinking=True)

    chat: Any = await CAIClient.chat.new_chat(character_id) # pyright: ignore[reportGeneralTypeIssues]

    tgt: str = chat["participants"][0 if not chat["participants"][0]['is_human'] else 1]['user']['username']

    response: Any = chat["messages"][0]
    charName, charAvatar, text = response["src__name"], response["src__character__avatar_file_name"], response["text"]

    embed = SuccessEmbed(charName, text)
    embed.set_author(name=charName, icon_url="https://characterai.io/i/400/static/avatars/"+charAvatar)
    embed.set_thumbnail(url="attachment://image.png")

    msg = await ctx.followup.send(content="Thread created for conversation!",
                                  embed=embed,
                                  file=File(utils.encodeImage((chat["external_id"], tgt.split(":")[1])), filename="image.png"),
                                  wait=True)
    await channel.create_thread(name=charName, message=Object(msg.id))

@CAITree.command(name="continue", description="Continue a conversation in a thread.")
@describe(prompt=f"the prompt to send to the character, maximum {MAX_CAI_MSG_LEN} characters.")
async def ask_character_ai_continue(ctx: Interaction, prompt: Range[str, None, MAX_CAI_MSG_LEN]):
    channel = ctx.channel
    if (not channel) or (channel.type != ChannelType.public_thread) or (not channel.parent) or (channel.parent.type != ChannelType.text):
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "This command must be run in a forum or thread."))
    create_task(ctx.response.defer(thinking=True))

    initMsg = channel.starter_message or await channel.parent.fetch_message(channel.id)
    url = initMsg.embeds[0].thumbnail.url
    if not url:
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "An unknown error occurred."))
    data = utils.decodeImage(BytesIO(get(url).content))
    history_id, tgt = data[0], data[1]

    response: Any = await CAIClient.chat.send_message(history_id, "internal_id:"+tgt, prompt) # type: ignore
    char: Any = response["src_char"]
    charName, charAvatar = char["participant"]["name"], char["avatar_file_name"]

    embed = SuccessEmbed(prompt[:255], response["replies"][0]["text"])
    embed.set_author(name=charName, icon_url="https://characterai.io/i/400/static/avatars/"+charAvatar)
    await ctx.followup.send(embed=SuccessEmbed(prompt[:255], response["replies"][0]["text"]))

askTree.add_command(CAITree)
tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")
    await gather(clientTask)

if __name__ == "__main__":
    run(main())