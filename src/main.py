import os
from pathlib import Path
from asyncio import create_task, gather, get_event_loop, run, CancelledError, InvalidStateError
from logging import basicConfig, FileHandler, StreamHandler, INFO, WARNING, ERROR, getLogger

from discord import Client, Embed, Intents, Interaction, Object, Thread
from discord.abc import PrivateChannel, GuildChannel
from discord.app_commands import CommandTree, Group, Range, describe
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import _ColourFormatter

from characterai import PyAsyncCAI
from datetime import datetime
from random import randint
from urllib.parse import urlparse
from httpx import get

from database import sql_execute # Can be used in /execute
import ai_cmds

os.chdir(Path(__file__).parent.parent)

logger = getLogger("skekbot" if __name__ == "__main__" else __name__)
info, warn, error = logger.info, logger.warn, logger.error

_ColourFormatter.LEVEL_COLOURS = [
    (INFO, '\033[94m'),
    (WARNING, '\033[93m'),
    (ERROR, '\033[91m'),
]

class SuccessEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.blue(), title=title, type=type, url=url, description=description, timestamp=timestamp)

class FailEmbed(Embed):
    def __init__(self, title: str | None = None, description: str | None = None, type: EmbedType = "rich", url: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.red(), title=title, type=type, url=url, description=description, timestamp=timestamp)

streamHandler = StreamHandler()
streamHandler.setFormatter(_ColourFormatter())
basicConfig(
    level=INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        FileHandler("logfile.pylog"),
        streamHandler
    ]
)

# // Intents
intents = Intents.none()
intents.message_content = True # // For What If and dad and some other things # type: ignore (for some reason, the type-checker hates this?)
intents.messages = True # // Same thing
intents.guilds = True # // The docs said it's a good idea to keep this enabled so...
intents.members = True # // So that we can know people's names
intents.guild_reactions = True # // We don't need to know about reactions in DMs, for Reaction Roles

OWNER_ID = 534828861586800676

CAIClient = PyAsyncCAI(os.environ["SKEKBOT_CHARACTERAI_TOKEN"])
client = Client(intents=intents)
tree = CommandTree(client)
command = tree.command

async def return_channel(id: int) -> Thread | GuildChannel | PrivateChannel:
    return client.get_channel(id) or await client.fetch_channel(id)

@client.event
async def on_ready():
    syncTask = create_task(tree.sync())
    await gather(syncTask)
    
@command(description="Allows the bot owner to run various debug commands.")
@describe(command="the python code to execute. See main.py for available globals.")
async def execute(ctx: Interaction, command: str):
    if ctx.user.id == OWNER_ID:
        await ctx.response.defer(thinking=True)

        returnVal = "Set returnVal to see output."
        command = f"async def main_exec(_locals): ctx = _locals['ctx']; {command}; _locals['returnVal'] = returnVal"
        _locals = locals()
        exec(command, globals(), _locals)
        await _locals["main_exec"](_locals)

        await ctx.followup.send(_locals["returnVal"])

@command(description="Great for making a bet and immediately regretting it.")
async def coin_flip(ctx: Interaction):
    await ctx.response.send_message("Heads!" if randint(0,1)==1 else "Tails!")

@command(description="$$ Transcribes an audio file or voice message.")
@describe(message_link="the full URL to the message. It must be a voice message, or have an audio attachment in the first position. And it must be <25MB.")
async def transcribe(ctx: Interaction, message_link: Range[str, 30, 100]):
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating transcription... This may take a while.")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    link_split = urlparse(message_link).path.split("/")

    msg, fail = None, False
    try: msg = next(x for x in client.cached_messages if x.id == link_split[4])
    except StopIteration: pass
    try: msg = msg or await client.get_partial_messageable(int(link_split[3])).fetch_message(int(link_split[4]))
    except IndexError: fail = True

    if fail or (not msg.attachments) or ((msg.attachments[0].content_type or "").split("/")[0] != "audio"): # type: ignore
        embed.title = "Transcription failed."
        embed.description = "Invalid message link."
        embed.color = Colour.red()
    else:
        transcription = await ai_cmds.transcribe(ctx.user.id, get(msg.attachments[0].url).content) # type: ignore
        if not transcription:
            embed.title = "Transcription failed."
            embed.description = "You do not have enough credits."
        else:
            embed.description = transcription 
            embed.title = "Transcription completed."

    await msgTask
    await msgTask.result().edit(embed=embed)

askTree = Group(name="ask", description="Chat with AI models.")
@askTree.command(name="gpt", description="$$ Chat with OpenAI's ChatGPT 3.5.")
@describe(prompt="the prompt to provide, up to 2048 characters.")
async def ask_gpt(ctx: Interaction, prompt: Range[str, None, 2048]):
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating response...")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    async def update(msg, failed):
        try:
            if failed:
                await msgTask
                return await msgTask.result().edit(embed=FailEmbed("Generation failed.", msg))
            embed.description = msg
            await msgTask.result().edit(embed=embed)
        except (CancelledError, InvalidStateError): pass
    
    await ai_cmds.chatGPT(ctx.user.id, prompt, update) # type: ignore TODO: This is nicht gut

@askTree.command(name="character_ai", description="Ask a character on Character.AI. You can find ID in the URL.")
@describe(prompt="the prompt to provide, up to 1024 characters.",
          character_id="can be found in the url: character.ai/chat?char=[ID IS HERE]?source=...")
async def ask_character_ai(ctx: Interaction, prompt: Range[str, None, 1024], character_id: Range[str, 43, 43]):
    await ctx.response.defer(thinking=True)
    chat = await CAIClient.chat.get_chat(character_id) # type: ignore

    participants = chat["participants"]
    tgt = participants[0 if not participants[0]['is_human'] else 1]['user']['username']

    response = await CAIClient.chat.send_message(chat["external_id"], tgt, prompt) # type: ignore
    char = response["src_char"]

    embed = SuccessEmbed(prompt[:255], response["replies"][0]["text"])
    embed.set_author(name=char["participant"]["name"], icon_url="https://characterai.io/i/400/static/avatars/"+char["avatar_file_name"]) # type: ignore
    
    await ctx.followup.send(embed=embed)

tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")
    await clientTask

if __name__ == "__main__":
    run(main())