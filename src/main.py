import os
from pathlib import Path
from asyncio import create_task, gather, run, CancelledError, InvalidStateError
from logging import basicConfig, FileHandler, StreamHandler, INFO, WARNING, ERROR, getLogger

from discord import Client, Embed, Intents, Interaction, Thread
from discord.abc import PrivateChannel, GuildChannel
from discord.app_commands import CommandTree, Group
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import _ColourFormatter

from datetime import datetime
from random import randint
from urllib.parse import urlparse

from httpx import get
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

client = Client(intents=intents)
tree = CommandTree(client)
command = tree.command

async def return_channel(id: int) -> Thread | GuildChannel | PrivateChannel:
    return client.get_channel(id) or await client.fetch_channel(id)

@client.event
async def on_ready():
    syncTask = create_task(tree.sync())
    await gather(syncTask)

@command(description="Great for making a bet and immediately regretting it.")
async def coin_flip(ctx: Interaction):
    await ctx.response.send_message("Heads!" if randint(0,1)==1 else "Tails!")

@command(name="transcribe", description="$$ Transcribes an audio file or voice message.")
async def transcribe(ctx: Interaction, message_link: str):
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
@askTree.command(name="gpt", description="$$ Chat with OpenAI's ChatGPT 3.5.") # type: ignore
async def ask_gpt(ctx: Interaction, prompt: str):
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

@askTree.command(name="character_ai", description="Ask a character on Character.AI. You can find ID in the URL. This command is unstable.")
async def ask_character_ai(ctx: Interaction, prompt: str, character_id: str):
    await ctx.followup.send(embed=FailEmbed("Not implemented", "This command doesn't work yet sorry"))

tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")
    await clientTask

if __name__ == "__main__":
    run(main())