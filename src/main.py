import os
from io import BytesIO
from pathlib import Path
from asyncio import create_task, gather, run, CancelledError, InvalidStateError
from logging import FileHandler, StreamHandler, getLogger
from sys import exc_info
from typing import Any, Optional

from discord import ChannelType, Client, Embed, File, HTTPException, Intents, Interaction, Message, Object, TextChannel, Thread, VoiceClient
from discord.app_commands import CommandTree, Group, Range, describe, check
from discord.app_commands.checks import cooldown
from discord.app_commands import AppCommandError, CommandInvokeError, BotMissingPermissions, CommandOnCooldown, MissingPermissions, CheckFailure
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import setup_logging, escape_mentions
from discord.utils import get as filter_one

from yaml import safe_load as yaml_safe_load
from characterai import PyAsyncCAI # pyright: ignore[reportMissingTypeStubs]
from datetime import datetime
from random import randint
from urllib.parse import urlparse
from httpx import get as http_get

from openai import AsyncOpenAI
from tiktoken import encoding_for_model
from time import time_ns
from pydub import AudioSegment # pyright: ignore[reportMissingTypeStubs]

import utils

os.chdir(Path(__file__).parent.parent)

setup_logging(handler=FileHandler("logfile.pylog"))
setup_logging(handler=StreamHandler())
logger = getLogger("skekbot")
info, warn, error = logger.info, logger.warning, logger.error

# Config
def decode_escape(data: str) -> str:
    return bytes(data, "utf-8").replace(b"\\n", b"\x0A").decode("utf-8")

with open("config.yaml") as file:
    config: Any = yaml_safe_load(file)

OWNER_ID = int(config["OWNER_ID"])
OWNER_NAME = decode_escape(config["OWNER_NAME"])

BOT_NAME = decode_escape(config["NAME"])
ABOUT_DESCRIPTION = decode_escape(config["DESCRIPTION"])
SOURCE_CODE = decode_escape(config["SOURCE_CODE"])
ABOUT_COPYRIGHT = decode_escape(config["COPYRIGHT"])

# Constants
SUPPORTED_TRANSCRIPTION_AUDIO_FORMATS = ["flac", "mp3", "mp4", "mpeg", "mpga", "m4a", "ogg", "wav", "webm"] # As per OpenAI documentation
MIN_DISCORD_MSG_LINK_LEN = 82  # Shortest possible link, 17 digit snowflakes
MAX_DISCORD_MSG_LINK_LEN = 91  # Longest possible link, 20 digit snowflakes
MAX_TRANSCRIBE_FILE_SIZE = 25  # Size in MB as per OpenAI documentation
MAX_CHATGPT_MSG_LEN = 2048     # Half of max output (which is both input and output combined)
MAX_CAI_MSG_LEN = 1024         # TODO: See the actual limit of CAI, this is arbitrary
CAI_ID_LEN = 43                # This is the exact length determined from various IDs

CHATGPT_THREAD_NAME = f"{BOT_NAME} ChatGPT Conversation"
CHARACTERAI_THREAD_NAME = f"{BOT_NAME} CharacterAI Conversation"

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
openAiClient = AsyncOpenAI(api_key=os.environ["SKEKBOT_OPENAI_TOKEN"])

class SuccessEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.blue(), title=title, type=type, url=url, description=description, timestamp=timestamp)

class FailEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.red(), title=title, type=type, url=url, description=description, timestamp=timestamp)

@client.event
async def on_error(event: str, *_):
    err = exc_info()[1]
    if isinstance(err, HTTPException):
        warn(f"{err} within {event}.")

@tree.error
async def on_app_command_error(ctx: Interaction, err: AppCommandError):
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

def find_any(string: str, subs: list[str], **kwargs: Any) -> Optional[tuple[int, str]]:
    "Returns the index returned by str.find() and the substring that was found."
    for sub in subs:
        pos = string.find(sub)
        if pos != -1:
            return (pos, sub)
    return None

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
        intersection_index = utils.first_intersection_index(split, ["i'm", "im", "i", "i’m"]) # Special condition for "i" - it needs to be followed by "am"
    if intersection_index is not None:
        startIndex = len(" ".join(split[:intersection_index[0]]))
        name = content[startIndex+len(intersection_index[1])+1:]
        name = escape_mentions(name.split(",")[0].split(".")[0][:50]).title().strip() # Stop at comma / period, max 50 characters
        if name != "": # Prevents bot triggering from just saying "I am" on it's own, or by giving a blank name
            tasks.append(create_task(msg.reply(f"Hi {name}, I'm dad!")))

    
    # Messages sent in certain threads are used for AI chat
    if channel.type == ChannelType.public_thread:
        assert isinstance(channel, Thread)

        if channel.name == CHATGPT_THREAD_NAME:
            embed = SuccessEmbed("Generating response...")
            msgTask = create_task(msg.reply(embed=embed))

            async def update(msg: str, failed: bool) -> Any:
                try:
                    if failed:
                        await msgTask
                        return await msgTask.result().edit(embed=FailEmbed("Generation failed", msg))
                    embed.description = msg
                    await msgTask.result().edit(embed=embed)
                except (CancelledError, InvalidStateError): pass

            inputTokens = len(encoding_for_model("gpt-3.5-turbo").encode(content))
            if not utils.hasEnoughCredits(author.id, "chat", inputTokens):
                return await update("You do not have enough credits to run this command.", True)
            
            messageHistory = [{
                "role": "system",
                "content": "You are in a public chat room. The current speaker is indicated by their name followed with their message. Don't mix people up. You are Assistant, but do not include your name in the response."
            }]

            history = [i async for i in channel.history(limit=10)]
            for i in history:
                if i.id == msg.id:
                    continue
                if i.author == client.user:
                    if i.embeds and i.embeds[0] and i.embeds[0].description:
                        messageHistory.insert(1, {
                            "role": "assistant",
                            "content": i.embeds[0].description
                        })
                else:
                    messageHistory.insert(1, {
                        "role": "user",
                        "content": f"{i.content[:MAX_CHATGPT_MSG_LEN]}"
                    })

            messageHistory.append({
                "role": "user",
                "content": f"{author.name}: {content}"
            })
            
            completion: Any = create_task(openAiClient.chat.completions.create(
                model="gpt-3.5-turbo",
                stream=True,
                messages=messageHistory # type: ignore
            )) # type: ignore
            
            outputTokens, response, lastTime = 0, "", time_ns() - 1_000_000_000
            async for chunk in await (completion):
                choice = chunk.choices[0]
                if choice.delta.content:
                    outputTokens += 1
                    response += (choice.delta.content or "")
                    if (lastTime + 1_000_000_000) > time_ns(): continue
                    lastTime = time_ns()
                    await update(response, False)
                if choice.finish_reason:
                    await update(response + (choice.delta.content or ""), False)
                    embed.title = "Generation completed!"
                    return utils.chargeUser(author.id, "chat", inputTokens, outputTokens)
                
        elif channel.name == CHARACTERAI_THREAD_NAME:
            assert isinstance(channel.parent, TextChannel)
            initMsg = (channel.starter_message) or (await channel.parent.fetch_message(channel.id))
            assert initMsg.embeds and initMsg.embeds[0] and initMsg.embeds[0].thumbnail
            url = initMsg.embeds[0].thumbnail.url
            if not url:
                return msg.reply(embed=FailEmbed("Command failed", "An unknown error occurred."))
            data = utils.decodeImage(BytesIO(http_get(url).content))
            history_id, tgt = data[0], data[1]

            response: Any = await CAIClient.chat.send_message(history_id, "internal_id:"+tgt, f"{author.name}: {content}") # type: ignore
            char: Any = response["src_char"]
            charName, charAvatar = char["participant"]["name"], char["avatar_file_name"]

            embed = SuccessEmbed("Generation completed!", response["replies"][0]["text"])
            embed.set_author(name=charName, icon_url="https://characterai.io/i/400/static/avatars/"+charAvatar)
            await msg.reply(embed=embed)

    await gather(*tuple(tasks))

@command(description="Allows the bot owner to run various debug commands.")
@describe(command="the python code to execute. See main.py for available globals.")
@check(lambda ctx: ctx.user.id == OWNER_ID)
async def execute(ctx: Interaction, command: str):
    if ctx.user.id == OWNER_ID:
        info(f"Attempting to execute command: {command}")
        await ctx.response.defer(thinking=True)

        command = f"""
async def main_exec(_locals):
    from database import sql_execute
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
    embed = SuccessEmbed(f"About {BOT_NAME}", ABOUT_DESCRIPTION)
    embed.add_field(name=ABOUT_COPYRIGHT, value="Licensed under [MPL v2.0](https://github.com/Skekdog/Skekbot/blob/main/LICENSE)")
    embed.add_field(name="Source Code", value=SOURCE_CODE)
    await ctx.response.send_message(embed=embed)

@command(description="Great for making a bet and immediately regretting it.")
@cooldown(2, 1)
async def coin_flip(ctx: Interaction):
    await ctx.response.send_message(utils.spoiler_pad(("Heads!" if randint(0, 1)==1 else "Tails!"), 6)) # 6 is the length of both results, future me!

@command(description="$$ Transcribes an audio file or voice message.")
@describe(message_link="the full URL to the message. It must be a voice message, or have an audio attachment as it's first attachment. And it must be <25MB.",
          language="the language to translate from."
)
@cooldown(1, 5)
async def transcribe(ctx: Interaction, message_link: Range[str, MIN_DISCORD_MSG_LINK_LEN, MAX_DISCORD_MSG_LINK_LEN], language: str) -> Any:
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

    msg = filter_one(client.cached_messages, id=msgId) or await client.get_partial_messageable(channelId).fetch_message(msgId)

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
    if not utils.hasEnoughCredits(ctx.user.id, "audio", duration): return

    utils.chargeUser(ctx.user.id, "audio", duration)

    data.seek(0)
    transcription = await openAiClient.audio.transcriptions.create(
        model="whisper-1",
        file=data,
        prompt="Uh... um... pffpfp...",
        response_format="text",
        language=language,
    )
    data.close()

    transcription = str(transcription)

    if not transcription:
        return await fail("You do not have enough credits.")
    
    embed.description = transcription
    embed.title = "Transcription completed"

    await msgTask
    await msgTask.result().edit(embed=embed)

askTree = Group(name="ask", description="Chat with AI models.")
@askTree.command(name="chat_gpt", description="$$ Chat with OpenAI's ChatGPT 3.5.")
@cooldown(1, 10)
async def ask_chatgpt(ctx: Interaction) -> Any:
    channel = ctx.channel
    if not channel or (channel.type != ChannelType.text):
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "This command must not be run in a forum or thread."))

    await ctx.response.defer()

    msg = await ctx.followup.send(content="Thread created for conversation! Messages sent in this thread will be sent to OpenAI for processing, along with your username. The thread name must not be changed, otherwise messages will no longer be sent.",
                                  #file=File(utils.encodeImage((chat["external_id"], tgt.split(":")[1])), filename="image.png"),
                                  wait=True)
    await channel.create_thread(name=CHATGPT_THREAD_NAME, message=Object(msg.id))


@askTree.command(name="characterai", description="Create a new chat with a CharacterAI. You can find their ID in the URL.")
@describe(character_id="can be found in the url: character.ai/chat?char=[ID IS HERE]?source=...")
@cooldown(1, 10)
async def ask_characterai(ctx: Interaction, character_id: Range[str, CAI_ID_LEN, CAI_ID_LEN]):
    channel = ctx.channel
    if not channel or (channel.type != ChannelType.text):
        return await ctx.response.send_message(embed=FailEmbed("Command failed", "This command must not be run in a forum or thread."))
    await ctx.response.defer(thinking=True)

    chat: Any = await CAIClient.chat.new_chat(character_id) # pyright: ignore[reportGeneralTypeIssues, reportCallIssue]

    tgt: str = chat["participants"][0 if not chat["participants"][0]['is_human'] else 1]['user']['username']

    response: Any = chat["messages"][0]
    charName, charAvatar, text = response["src__name"], response["src__character__avatar_file_name"], response["text"]

    embed = SuccessEmbed(charName, text)
    embed.set_author(name=charName, icon_url="https://characterai.io/i/400/static/avatars/"+charAvatar)
    embed.set_thumbnail(url="attachment://image.png")

    await CAIClient.chat.send_message(chat["external_id"], tgt, "This is a public chat room. Separate users will be indicated by their username, followed by a colon. e.g, 'Joe: Hi!'") # type: ignore

    msg = await ctx.followup.send(content="Thread created for conversation! Messages sent in this thread will be sent to CharacterAI for processing, along with your username. The thread name must not be changed, otherwise messages will no longer be sent.",
                                  embed=embed,
                                  file=File(utils.encodeImage((chat["external_id"], tgt.split(":")[1])), filename="image.png"),
                                  wait=True)
    await channel.create_thread(name=CHARACTERAI_THREAD_NAME, message=Object(msg.id))

tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")
    await gather(clientTask)

if __name__ == "__main__":
    run(main())