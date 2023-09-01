from enum import Enum
from discord import Embed,Colour

class GPT_Model(Enum):
    GPT3 = "gpt-3.5-turbo"
    # GPT4 = "gpt-4" # // When used for what if, Gpt-4 worked out to be THIRTY times more expensive. it's a no-go.
                     # // I suppose I'll keep this enum if ever a new model is released or gpt4 is cheaper.

    def __str__(self):
        return self.value

class Image_Mode(Enum):
    GENERATE = 0
    VARIATE = 1

# // Vs code colours constant variables a darker blue if they are all caps :smiley:
DAILY_BUDGET = 0.05
PRICES = {
    GPT_Model.GPT3: [0.0015,0.0020], # // Input tokens cost $0.0015 per 1000, Output tokens cost $0.002 per 1000
    "1024x1024": 0.0200,
    "256x256": 0.016,
}

OWNER_ID,BOT_IDS = 534828861586800676,[1054474727642628136,1111975854839435376] # // Skekbot and Skestbot respectively

NOBODY = "Nobody"
ROCK,PAPER,SCISSORS = "Rock","Paper","Scissors"
RPS_CHOICES = [ROCK,PAPER,SCISSORS]

RE_USER_MENTION = "<@!?(\d{17,19})>"

# // Frequently used texts, where it also either improves or doesn't hurt readability
BLANK = ""
TEXT_DF = "Download Failed."
TEXT_DF_CMD_RT = "Failed to download command data. Try again later."
ERR_NO_FIX = "An error occurred. And it likely won't be fixed if you try again."
DATA_ATTACHMENT = "attachment://data.png"
GENERATING_RESPONSE = "Generating a response..."

class SuccessEmbed(Embed):
    def __init__(self,title:str=None,description:str=None):
        super().__init__(title=title,colour=Colour.blue(),description=description)
class FailEmbed(Embed):
    def __init__(self,title:str=None,description:str=None):
        super().__init__(title=title,colour=Colour.red(),description=description)

# // Embeds - common embeds with consistent titles and descriptions
INVALID_INTERACTION = FailEmbed("Invalid Interaction.","What did you do???")
NO_THREAD_CMD = FailEmbed("Command Failed.","You cannot run this command in a thread.")
NO_PERMISSION = FailEmbed("Interaction Failed.","You do not have permission to use this.")

REGEN_FAILED = FailEmbed("Regeneration Failed.",ERR_NO_FIX)
REGEN_COOLDOWN = FailEmbed("Awaiting Cooldown.","You must wait a few seconds before regenerating a prompt. Try again later.") # // Other cooldowns are silently ignored

DOWNLOAD_FAILED = FailEmbed(TEXT_DF,ERR_NO_FIX)
DOWNLOAD_FAILED_TEMP = FailEmbed(TEXT_DF,"An error occurred. Try again later.")
DOWNLOAD_FAILED_DM = FailEmbed(TEXT_DF,"Failed to send DM! Make sure you haven't blocked Skekbot and that you have DMs from server members enabled.")

INVALID_MESSAGE_LINK = FailEmbed("Transcription Failed.","Please provide a valid message link (accessible by Skekbot and not a message id).")
INVALID_VOICE_MESSAGE = FailEmbed("Transcription Failed.","The message you provided does not appear to have a voice message.")

THREAD_CREATED = SuccessEmbed("Thread Created.","Send a message in the thread to continue the conversation.")

ABOUT_DESCRIPTION = r"""
Use </help:1145022212290658434> for a list of commands and how to use them.

Skekbot is a just for fun Discord bot, developed by Skekdog using the [discord.py](https://www.github.com/Rapptz/discord.py) library.
Skekbot makes use of several other third-party services including, but not limited to: [OpenAI](https://www.openai.com), [CharacterAI](https://www.character.ai), [Node-CharacterAI](https://www.github.com/realcoloride/node_characterai) and [DeepL](https://www.deepl.com).
Skekbot is FOSS software, the source code is publicly available on [GitHub](https://www.github.com/Skekdog/Skekbot). Be aware that what is currently running may be different from the source.

Thanks for using Skekbot!
"""
ABOUT_EMBED = SuccessEmbed("About Skekbot",ABOUT_DESCRIPTION)
ABOUT_EMBED.add_field(name="Copyright Skekdog © 2023",value="Licensed under the GNU General Public License v3.0.\nSee [LICENSE](https://github.com/Skekdog/Skekbot/blob/main/LICENSE) for more info.",inline=True)
ABOUT_EMBED.add_field(name="Contact",value="If you wish to contact me, either send a DM to @skekdog on Discord or email skekdog@gmail.com.",inline=True)
ABOUT_EMBED.add_field(name="Data Usage",value="[Privacy Policy](https://www.github.com/Skekdog/Skekbot/blob/main/PRIVACY.md)",inline=True)

# // Flavour triggers
APOSTROPHES = [BLANK,"'","‘","’","'","'"]
DAD_TRIGGERS = ["i"+i+"m" for i in APOSTROPHES]
WHAT_TRIGGERS = ["what"+i+"s up" for i in APOSTROPHES]+["what is up"]
ARTICLES = ["a","an","the"]

UNWELCOMES = [938487223081402388]

D_UP = { # // This used to be a separate file, but there is no need to have it as that. Only makes it more prone to issues because I can't code
    534828861586800676: [0.05],
    691918664546516992: [0.02],
}
D_UD = "userdata"
D_SS = "serversettings"
D_RR = "reactionroles"
D_PL = "polls" # // Not to be confused with poland

NAMES = ["Sarah","Michael","Emily","Christopher","Ryan","Brittany",
         "Nicholas","Heather","Jacob","Katie","Sakura","Luis","Elena",
         "Hans","Amir","Ana","Johan","Leila","Pablo","Aisha","Lucky",]

DEFAULT_PERSONALITY = "The user is {USERNAME} you are {BOTNAME}"
PERSONALITIES = {
    # // Format: personality: [SystemMessage, Description, Emoji, ID[0-255]]
    None: ["","","",0],
    "balanced": ["","Standard ChatGPT.","⚖",1],
    "drunk": ["Drunk Your responses are slurred and sometimes extreme and should include references to alcohol {DEFAULT}","Extremely intoxicated.","🥴",2],
    "snarky": ["Very sarcastic Respond with a huge level of sarcasm and wit You may insult the user in a hilarious manner {DEFAULT}","Extremely sarcastic.","🙄",3],
    "stupid": ["Dumb Respond with blatantly incorrect information yet confidently {DEFAULT}","Extremely stupid.","🤪",4],
    "philosophical": ["{DEFAULT} You are a philosopher take the users prompt and break it down philosophically For example What is your name - A name is","What is love?","🤔",5],
    "military": ["You are a military general responses must incorporate usage of heavy military power {DEFAULT}","Baby don't hurt me.","💂‍♂️",6],
}

ABC = ["A","B","C"]
NC_BOARD = r"""
` | | `
` | | `
` | | `
"""

STITCHBORDERPX = 10

# // I wish these were actual cats
# // This text is shown in /help
CMD_CATS = {
    "None": "",
    "OpenAI": "All commands in this section use OpenAI's service and require credits. See /credits for more information.",
    "Games": "Some fun.",
    "Other": "These commands don't fit into any other category."
}

ERR_OCCURRED = "An error occurred."