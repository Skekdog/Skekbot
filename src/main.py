import os
from pathlib import Path
from asyncio import create_task, gather, run, CancelledError, InvalidStateError
from logging import basicConfig, FileHandler, StreamHandler, INFO, WARNING, ERROR, getLogger

from discord import Client, Embed, Intents, Interaction
from discord.app_commands import CommandTree, Group
from discord.colour import Colour
from discord.types.embed import EmbedType
from discord.utils import _ColourFormatter

from datetime import datetime
from random import randint

from ai_cmds import chatGPT

os.chdir(Path(__file__).parent.parent)

logger = getLogger("skekbot" if __name__ == "__main__" else __name__)
info, warn, error = logger.info, logger.warn, logger.error

_ColourFormatter.LEVEL_COLOURS = [
    (INFO, '\033[94m'),
    (WARNING, '\033[93m'),
    (ERROR, '\033[91m'),
]

class SuccessEmbed(Embed):
    def __init__(self, title: str | None = None, type: EmbedType = "rich", url: str | None = None, description: str | None = None, timestamp: datetime | None = None):
        super().__init__(colour=Colour.blue(), title=title, type=type, url=url, description=description, timestamp=timestamp)

class FailEmbed(Embed):
    def __init__(self, title: str | None = None, type: EmbedType = "rich", url: str | None = None, description: str | None = None, timestamp: datetime | None = None):
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

@client.event
async def on_ready():
    syncTask = create_task(tree.sync())
    await gather(syncTask)

@command(description="Great for making a bet and immediately regretting it.")
async def coin_flip(ctx: Interaction):
    await ctx.response.send_message("Heads!" if randint(0,1)==1 else "Tails!")

askTree = Group(name="ask", description="Chat with AI models.")
@askTree.command(name="gpt", description="Chat with OpenAI's ChatGPT 3.5.")
async def ask_gpt(ctx: Interaction, prompt: str):
    create_task(ctx.response.defer(thinking=True))

    embed = SuccessEmbed("Generating response...", description="")
    msgTask = create_task(ctx.followup.send(embed=embed, wait=True))

    async def update(msg, failed):
        try:
            if failed:
                await msgTask
                return await msgTask.result().edit(embed=FailEmbed("Generation failed.", description=msg))
            embed.description = msg
            await msgTask.result().edit(embed=embed)
        except (CancelledError, InvalidStateError): pass
    
    await chatGPT(ctx.user.id, prompt, update) # type: ignore TODO: This is nicht gut
    
tree.add_command(askTree)

async def main():
    clientTask = create_task(client.start(os.environ["SKEKBOT_MAIN_TOKEN"]))
    info("Client starting...")
    await clientTask

if __name__ == "__main__":
    run(main())