import discord
from discord.app_commands.errors import *
from discord.app_commands.checks import cooldown
from discord.app_commands import command
from discord.app_commands import describe
from discord.app_commands import choices
from discord.app_commands import Choice
from discord.app_commands import Range
from discord.app_commands import Group
from discord import ChannelType
from discord import Interaction
from discord import Message
from discord import Object

import skekcommands
from skekcommands import *
from skekcommands import _AICommands
from utils import readFromKey
from generatewhatif import generate

import inspect
import os

p = "polls"
rr = "reactionroles"

import openai,asyncio
openai.api_key = os.environ.get("TOKEN_OPENAI")

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

cIDs = {
    "Shrek": "eX2BOqEshHs_G4TOisfotuDRi5nNt6fVP9DHrxk8A04",
    "Margaret Thatcher": "_zTwmoG1MDFcLxB-v6bcrqQPpN8DnXknPPDj3yWy4MY",
    "Boeing 747": "oUipEQvbc9bV3iv_ZLNgTjJYv0hHs4Nd2gklZtzJ9yw",
    "Joe Biden": "dSo0so5PT_NJXK_QgWOr_V8Gz461c6n-BQdRvS1qjhc",
    "Donald Trump": "BAatpD6zHNv9j4_b7f-47bfDNjWYKNlCRPT0yXxqOhQ",
    "Obama": "4oN2qlGnBIheSXosJEYyy148-GRr6L5tOmUOPC9Zggo",
    "Joseph Stalin": "zQPkBj9Arxmsq0P6ENO1JCyz5A8_kh7izZYjQfmoVx0",
    "Barry": "LsejHKO81UHXi1kB0Fs6iwS5SOV7NnL4vugvjtLdJXk",
    "Senator Armstrong": "BEnOzGNydJ73zgv6FtauylH8RZIxVhdDONGGeSSIQRw",
    "God": "pZdRSfgxtc6l-KlrbWkAp5b9djOmP3L3NpN45AF3xgI",
    "Putin": "ycbgWJyXmcVFZc0vyF3AaI1tLWLHTVhbTZFENC9Ie6w",
    "Rasputin": "TgvuoP8-n60LCIH644oe-G56zKDpPKXHtGEFnhN7V10",
    "Elizabeth II": "4YauQqfIaIQfYfg0EqL7K67T6u2RK6xAo7d5QTcVyYg",
    "Liz Truss": "B4lYjyGEsLuAMQB-4tiB8b-SSN609r1h-R0dJNhc79A",
    "Boris Johnson": "vJLaNMpOGtMSy8huxOAAuLapCP_jdU98oMvCbfB603o",
    "Terraria Guide": "yXldD-2l-vmlBC4Njc9PMrNwxrK1T5QxcoxX7o5zuWY",
    "Agent 47": "kqBCsNft0PU2IbrFQ9r4InAQWBh7Y5yLhxR8z-B9g-Y",
    "Elon Musk": "6HhWfeDjetnxESEcThlBQtEUo0O8YHcXyHqCgN7b2hY",
    "Mark Zuckerberg": "_C4S3uthPA8ZSH5LrWM9JNVdtlZq-iqhniamLtixQy8",
    "Teddy Roosevelt": "HT6weIr7pzBQ0dGRmzML0laf1ZrJXk_U2vTAxEEWz9c",
    "Abraham Lincoln": "sXiTYQw119NhyPp7vBTT0MuQDssS7VKOcPEW2f6emBc",
    "Ronald McDonald": "r9Mfy4bTaipFAZo_fkTYG6BSi4Z-jsarEzd4hjUjr3g",
    "Spongebob": "JCcce8JGM3fL2aVARXjng7ADYTxo45gwj3XAROiuxnE",
    "Franklin Framed": "iHMpcc8cs5tF4dCY1-TtqzbiL67xRS6Y6S1IbPQgNrU"
}

server1 = 920370076035739699
server2 = 1051204758842658916
isTest = (os.environ.get("ISHOSTED") is None)

intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = False
intents.voice_states = False
intents.webhooks = False
intents.invites = False
intents.typing = False

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@tree.error
async def on_app_command_error(ctx:Interaction,err:AppCommandError):
    print(err)
    match err.__class__.__name__:
        case "CommandOnCooldown":
            await ctx.response.send_message(f"You must wait {str(round(err.retry_after,2))}s before using this command again.",ephemeral=True)
        case "TransformerError":
            await ctx.response.send_message(f"Failed to convert {err.value} to {str(err.type)}",ephemeral=True)
        case "NoPrivateMessage":
            await ctx.response.send_message(f"You may not run this command in a DM.")
        case "MissingRole":
            await ctx.response.send_message(f"You are missing the {err.missing_role} role to use this command.",ephemeral=True)
        case "MissingAnyRole":
            await ctx.response.send_message(f"You are missing one or more of the required roles to use this command: {str(err.missing_roles)}",ephemeral=True)
        case "MissingPermissions":
            await ctx.response.send_message(f"You are missing the required permissions to use this command. ({str(err.missing_permissions)})",ephemeral=True)
        case "BotMissingPermissions":
            await ctx.response.send_message(f"Skekbot does not have the required permissions ({str(err.missing_permissions)}) to execute this command, please contact the server owner.",ephemeral=True)
        case _:
            await ctx.response.send_message(f"An unknown error occcured when executing this command. Try again later.",ephemeral=True)

@client.event
async def on_ready():
    await tree.sync()
    if not isTest:
        await tree.sync(guild=Object(server1))
        await tree.sync(guild=Object(933989654204649482))
    print("Readied!")

generatePrompt = "Creative no matter how illogical the prompt"
userPromptTragedy = " Remember this all just for fun sometimes the story should have a tragic end the story should be only 3 paragraphs start in middle of action"
userPrompt = " Remember this all just for fun should be only 3 paragraphs start in middle of action"
userPrompts = [userPromptTragedy,userPrompt]

@client.event
async def on_message(msg:Message):
    auth = msg.author
    if auth == client.user or auth.id == 1111975854839435376 or auth.id == 1054474727642628136:
        return
    
    chan = msg.channel
    cont = msg.content
    con = cont.lower()

    ##Hi dad
    foundIm = False
    name = ""
    prev = ""
    for i in cont.split(" "):
        if foundIm:
            name += i+" "
        else:
            i = i.lower()
            if (i in ["im","i'm","i’m"]) or ("i am" == prev+" "+i):
                foundIm = True
            prev = i
    if name != "":
        name = name.replace("@","@​")
        await msg.reply(content=f"Hi {(name[:-1])[:1950]}, I'm dad!",mention_author=False,silent=True)

    ##Not now
    if msg.guild:
        if server1 == msg.guild.id:
            if con.find("not now")>-1:
                await msg.reply(content="Not now",mention_author=False)
            elif con.find("doors")>-1:
                await msg.reply(content="Not now",mention_author=False)

    strip = con.strip()
    if strip == "what if" or strip == "but what if":
        prevMsg = ""
        if strip == "but what if":
            for mesg in [i async for i in chan.history()]:
                if mesg.content.lower().strip() != "but what if":
                    if mesg.author.id == skekbotID or mesg.author.id == skestbotID:
                        if mesg.embeds[0]:
                            prevMsg = mesg.embeds[0].title[3:63]
                            break
                        else:
                            prevMsg = mesg.content[:60]
                    else:
                        prevMsg = mesg.content[:60]
                        break
        scenario = generate()
        scen = scenario
        if prevMsg != "":
            scen = prevMsg+" but then "+scenario[0].lower()+scenario[1:]
        newMsg = await chan.send(content="Generating a scenario...",reference=msg,mention_author=False)
        response = None
        cost = 0

        embed = discord.Embed(colour=discord.Colour.red(),title=scen[0].upper()+scen[1:250]+("..." if scen[:250] != scen else ""))
        try:
            random.shuffle(userPrompts)
            response = await asyncio.to_thread(openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                temperature=1,
                max_tokens=384,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                user="1723",

                messages = [
                    {"role":"system","content":generatePrompt,
                    "role":"user","content":scen+userPrompts[0]
                    }
                ]
            )
            embed.colour = discord.Colour.blue()
            cost = getCost(AI_API.Chat,response.usage.total_tokens)
            response = "```"+response.choices[0].message["content"]+"```"

        except BaseException as err:
            response = "An unknown error occurred whilst generating this scenario. Try using some other OpenAI commands, such as </ask gpt:1095068823759093831>, or try again later. \n\nError: "+str(err)

        content = "Generated the tale of the time when "+scen
        if len(response) < 200:
            content = "This scenario probably failed to generate."
            embed.colour = discord.Colour.red()
        embed.description = response
        embed.add_field(name="This cost Skekbot ${0:.4f}.".format(cost),value="But you got it for free.")
        await newMsg.edit(content=content,embed=embed)

    if chan.type == ChannelType.public_thread:
        if chan.name.find(" | ") > -1:
            md = chan.name.split(" | ")
            botName = md[2]
            personalityStr = md[1]
            if auth.id == int(md[3]):
                sysMsg = sysMsgs[AI_Personality[personalityStr]].format(auth.name,botName)
                pastMsgs = [{"role":"system","content":sysMsg}]
                msgs = [message async for message in chan.history(oldest_first=True)]
                for pastMsg in msgs:
                    if pastMsg.author == client.user:
                        if len(pastMsg.embeds) == 0 or not pastMsg.content:
                            continue
                        embed = pastMsg.embeds[0]
                        if embed.colour != discord.Colour.blue():
                            continue
                        pastMsgs.append({"role":"assistant","content":embed.description[3:-3]})
                    elif pastMsg.author == auth:
                        pastMsgs.append({"role":"user","content":pastMsg.content})
                msg = await msg.reply("Processing... this may take a while.")
                await _AICommands(None,cont,AI_API.Chat,
                                            userId=auth.id,userName=auth.name,channel=chan,msg=msg,editFunc=msg.edit,
                                            chatOverride=pastMsgs,
                                            botName=botName,
                                            personality=personalityStr)

    if auth.id == 658762325993717802:
        await msg.reply(content="Shut up nobody cares",mention_author=False)

async def reactionRoles(reactRoles,event_type,reaction,user):
    if reactRoles and reaction:
        rolesToAssign = []
        for i in reactRoles:
            vals = i[1:-1].split(",")
            em,roleId = emoji.emojize(vals[0]),vals[1]
            if em == reaction.emoji:
                rolesToAssign.append(Object(roleId))
                break
        if len(rolesToAssign) > 0:
            if event_type == "REACTION_ADD":
                await user.add_roles(*tuple(rolesToAssign))
            else:
                await user.remove_roles(*tuple(rolesToAssign))

@client.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    guild = await client.fetch_guild(payload.guild_id)
    user = await guild.fetch_member(payload.user_id)
    if user == client.user:
        return
    
    chan = await guild.fetch_channel(payload.channel_id)
    msgId = payload.message_id
    msg = await chan.fetch_message(msgId)

    react:discord.Reaction = None
    for i in msg.reactions:
        if i.emoji == payload.emoji.name:
            react = i
            break

    val = readFromKey(p,msgId,"pollCreator,expiryValue,expiryCondition")
    if val[0]:
        if react:
            if react.me:
                if int(val[0]) == user.id:
                    await react.remove(user)
                    await user.send("You can't vote on your own poll!")
                    return

                for i in msg.reactions:
                    if i.emoji != react.emoji and i.me:
                        async for x in i.users():
                            if user.id == x.id:
                                await react.remove(user)
                                await user.send("You can't vote more than once on a poll! If you would like to change your vote, first remove your previous vote.")
                                return
                
            if val[2] == 0:
                total = 0
                counts = {}
                for i in msg.reactions:
                    if i.me:
                        total += (i.count-1)
                        counts[i.emoji] = i.count-1

                top = 0
                winner = ""
                for i in counts:
                    if counts[i] > top:
                        top = counts[i]
                        winner = i

                if total >= int(val[1]):
                    deleteKey(p,msg.id)
                    overallResults = "Overall results:\n"
                    for i,v in counts.items():
                        overallResults += f"{str(i)}: {str(v)} votes\n"
                    await msg.edit(content=f"Poll concluded at <t:{round(time.time())}:F>!\nThe winning option was {winner} with {top} vote(s).\n{overallResults}")

    r = readFromKey(rr,msgId,"data")[0]
    if r:
        reactRoles = r.split("[]")
        await reactionRoles(reactRoles,payload.event_type,react,user)

@client.event
async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
    guild = await client.fetch_guild(payload.guild_id)
    user = await guild.fetch_member(payload.user_id)
    if user == client.user:
        return
    
    chan = await guild.fetch_channel(payload.channel_id)
    msgId = payload.message_id
    msg = await chan.fetch_message(msgId)

    react:discord.Reaction = None
    for i in msg.reactions:
        if i.emoji == payload.emoji.name:
            react = i
            break

    reactRoles = readFromKey(rr,msgId,"data")[0].split("[]")
    await reactionRoles(reactRoles,payload.event_type,react,user)


@tree.command(name="imagine",description="Generate images using DALL-E 2.")
@cooldown(rate=1,per=10)
@describe(prompt="Prompt to provide to DALL-E 2.",amount="Amount of images to generate. Cost of each image depends on resolution. If generating in 1024x1024 resolution, there is a max amount of 2 images due to Discord limitations.",resolution="Resolution of each image. 256x256 costs $0.016 per image, 512x512: $0.018, 1024x1024: $0.02.")
@choices(resolution=[Choice(name="1024x1024",value="1024x1024"),Choice(name="512x512",value="512x512"),Choice(name="256x256",value="256x256")],
         amount=[Choice(name="1",value=1),Choice(name="2",value=2),Choice(name="3",value=3),Choice(name="4",value=4)])
async def imagine(ctx,prompt:str,amount:int=1,resolution:str="256x256"):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await imagineCMD(ctx,prompt,amount,resolution)


@tree.command(name="variations",description="Generate variations of an uploaded image using DALL-E 2. Variations are 1024x1024.")
@cooldown(rate=1,per=10)
@choices(amount=[Choice(name="1",value=1),Choice(name="2",value=2),Choice(name="3",value=3),Choice(name="4",value=4)])
async def variations(ctx:Interaction,image:discord.Attachment,amount:int=1):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await _AICommands(ctx,None,AI_API.Variation,resolution=Resolution.High,amount=amount,variations_image=image)


@tree.command(name="credits",description="Learn more about the credits system, and view your current credits.")
async def credits(ctx):
    await creditsCMD(ctx)


@tree.command(name="lucky",description="Fortunes.")
async def lucky(ctx):
    await luckyCMD(ctx)


@tree.command(name="ask_lucky",description="Ask Lucky AI. Does not cost credits.",guilds=[Object(server1)])
@cooldown(rate=1,per=1)
@describe(prompt="Prompt to provide Lucky.")
async def ask_lucky(ctx:Interaction,prompt:str):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await askCMD(ctx,prompt,AI_API.Lucky)


@tree.command(name="speech_synthesis",description="Use ElevenLabs to synthesise speech. Max of 250 characters per day.")
@cooldown(rate=1,per=15)
@describe(prompt="Prompt to synthesise speech out of.",model="Voice model to use.",multilingual="Use the multilingual model.")
@choices(
    model=[
        Choice(name="Adam",value="Adam"),
        Choice(name="Antoni",value="Antoni"),
        Choice(name="Arnold",value="Arnold"),
        Choice(name="Josh",value="Josh"),
        Choice(name="Sam",value="Sam"),
        Choice(name="Bella",value="Bella"),
        Choice(name="Domi",value="Domi"),
        Choice(name="Elli",value="Elli"),
        Choice(name="Rachel",value="Rachel")
    ]
)
async def speech_synthesis(ctx:Interaction,prompt:str,model:str,multilingual:bool=False):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await synthesisCMD(ctx,prompt,model,multilingual)

@tree.command(name="coin_flip",description="Flip an unbiased coin.")
async def coin_flip(ctx):
    await coin_flipCMD(ctx)

@tree.command(name="rps",description="Rock, paper, scissors!")
async def rps(ctx,opponent:discord.Member):
    await rpsCMD(ctx,opponent)

@tree.command(name="translate",description="Translate things. Due to a discord limitation, languages need to be split into 2 lists.")
@cooldown(rate=1,per=1)
@choices(new_language=[Choice(name=v[1],value=v[0]) for i,v in enumerate(deepLLanguageCodes.items()) if i < 25],
         new_language_2=[Choice(name=v[1],value=v[0]) for i,v in enumerate(deepLLanguageCodes.items()) if i >= 25])
@describe(suffocating_letters="The text to translate.",new_language="The language to translate the suffocating letters into.",new_language_2="The language to translate into, if it is not available in the first option.")
async def translate(ctx:Interaction,suffocating_letters:Range[str,1,900],new_language:str,new_language_2:str=None):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await translateCMD(ctx,suffocating_letters,target_lang=new_language_2 if new_language_2 else new_language)

@tree.context_menu(name="Reaction Roles")
@cooldown(rate=1,per=0.1)
async def reaction_roles(ctx:Interaction,msg:Message):
    if ctx.user.guild_permissions.manage_roles:
        await reaction_rolesCMD(ctx,msg)
        return
    await ctx.response.send_message("You require the `manage_roles` permission to use this command.",ephemeral=True)

@tree.context_menu(name="Translate to English")
@cooldown(rate=1,per=1)
async def translate(ctx:Interaction,msg:Message):
    await ctx.response.defer(thinking=True,ephemeral=False)
    await translateCMD(ctx,msg.content)


class Converse(Group):
    @command(name="gpt",description="Ask OpenAI's ChatGPT Chat model. Good all round, but more expensive.")
    @cooldown(rate=1,per=30)
    @describe(prompt="Prompt to provide the AI.",personality="The personality of the AI.",
              temperature="How deterministic the response will be.",presence_penalty="Penalty to apply to the AI for not starting new topics.",
              frequency_penalty="Penalty to apply to the AI for repeating the same words.")
    @choices(personality=[Choice(name="Random",value="Random"),
                          Choice(name="Balanced",value="Balanced"),
                          Choice(name="Drunk",value="Drunk"),
                          Choice(name="Snarky",value="Snarky"),
                          Choice(name="Serious",value="Serious"),
                          Choice(name="Stupid",value="Stupid"),
                          Choice(name="Creative",value="Creative"),
                          Choice(name="Sentient",value="Sentient"),
                          Choice(name="Philosophical",value="Philosophical"),
                          Choice(name="Military",value="Military"),])
    async def converse_gpt(self,ctx:Interaction,prompt:str,personality:str,temperature:Range[float,0,1]=0.7,presence_penalty:Range[float,-2,2]=0.7,frequency_penalty:Range[float,-2,2]=0.6):
        if ctx.channel.type == ChannelType.public_thread:
            await ctx.response.send_message("You may not use this command in a thread.",ephemeral=False)
            return
        await ctx.response.defer(thinking=True,ephemeral=False)
        await converseCMD(ctx,prompt,AI_API.Chat,personality=personality,randomness=temperature,presence=presence_penalty,frequency=frequency_penalty)
tree.add_command(Converse())

class Ask(Group):
    
    @command(name="gpt",description="Ask OpenAI's ChatGPT Chat model. Good all round, but more expensive.")
    @cooldown(rate=1,per=3)
    @describe(prompt="Prompt to provide the AI.",personality="The personality of the AI.",
              temperature="How deterministic the response will be.",presence_penalty="Penalty to apply to the AI for not starting new topics.",
              frequency_penalty="Penalty to apply to the AI for repeating the same words.")
    @choices(personality=[Choice(name="Random",value="Random"),
                          Choice(name="Balanced",value="Balanced"),
                          Choice(name="Drunk",value="Drunk"),
                          Choice(name="Snarky",value="Snarky"),
                          Choice(name="Serious",value="Serious"),
                          Choice(name="Stupid",value="Stupid"),
                          Choice(name="Creative",value="Creative"),
                          Choice(name="Sentient",value="Sentient"),
                          Choice(name="Philosophical",value="Philosophical"),
                          Choice(name="Military",value="Military"),])
    async def ask_gpt(self,ctx,prompt:str,personality:str,temperature:Range[float,0,1]=0.7,presence_penalty:Range[float,-2,2]=0.7,frequency_penalty:Range[float,-2,2]=0.6):
        try:
            await ctx.response.defer(thinking=True,ephemeral=False)
        except discord.errors.NotFound:
            return
        await askCMD(ctx,prompt,AI_API.Chat,personality=personality,randomness=temperature,presence=presence_penalty,frequency=frequency_penalty)

    
    @command(name="babbage",description="Ask OpenAI's Babbage Completion model. Good at completing sentences or patterns, cheaper.")
    @cooldown(rate=1,per=3)
    @describe(prompt="Prompt to provide the AI.",temperature="How deterministic the response will be.",
              presence_penalty="Penalty to apply to the AI for not starting new topics.",frequency_penalty="Penalty to apply to the AI for repeating the same words.")
    async def ask_babbage(self,ctx,prompt:str,temperature:Range[float,0,1]=0.7,presence_penalty:Range[float,-2,2]=0.7,frequency_penalty:Range[float,-2,2]=0.6):
        await ctx.response.defer(thinking=True,ephemeral=False)
        await askCMD(ctx,prompt,AI_API.Completion,randomness=temperature,presence=presence_penalty,frequency=frequency_penalty)

    
    @command(name="character_ai",description="Ask a character on CharacterAI. Does not cost credits.")
    @cooldown(rate=1,per=1)
    @describe(prompt="Prompt to provide the AI.",character_id="ID of the character you want to ask. This is found in the url of a character: chat?char=ID.")
    async def ask_character_ai(self,ctx,prompt:str,character_id:str):
        await ctx.response.defer(thinking=True,ephemeral=False)
        try:
            await askCMD(ctx,prompt,AI_API.CharacterAI,character_id=character_id)
        except discord.app_commands.errors.CommandInvokeError as err:
            await ctx.followup.send("An error occurred.")

    cAIGroup = Group(name="character_ai_",description="Ask a character on CharacterAI. Does not cost credits.")
    @cAIGroup.command(name="preset",description="Ask a preset character.")
    @describe(prompt="Prompt to provide the AI.",character="Character preset to use.")
    @cooldown(rate=1,per=1)
    @choices(character=[Choice(name=i[0],value=i[1]) for i in cIDs.items()])
    async def ask_character_ai_presets(self,ctx,prompt:str,character:str):
        await ctx.response.defer(thinking=True,ephemeral=False)
        try:
            await askCMD(ctx,prompt,AI_API.CharacterAI,character_id=character)
        except discord.app_commands.errors.CommandInvokeError as err:
            await ctx.followup.send("An error occurred.")
tree.add_command(Ask())

class Poll(Group):
    
    @command(name="create",description="Create a poll.")
    @cooldown(rate=1,per=10)
    @describe(question="Question to poll on.",options="A list of options to vote on, separated by semicolons (;). Example: `Fish;Horse`",expirymode="Under what condition should the poll finish?",expiryvalue="Value for when the poll should conclude. Either an amount of minutes from now, or an amount of total reactions.")
    @choices(expirymode=[Choice(name="upon reaching X total reactions",value="reactions")])
    #@choices(expirymode=[Choice(name="after X minutes",value="time"),Choice(name="upon reaching X total reactions",value="reactions")])
    
    async def poll_create(self,ctx:Interaction,question:str,options:str,expirymode:str,expiryvalue:int):
        await pollCMD(ctx,"create",question,options,expirymode,expiryvalue)
tree.add_command(Poll())



@tree.command(name="help",description="Learn more about Skekbot commands here.")
@cooldown(rate=1,per=3)
@describe(command="Command to provide information on.")
@choices(command=[Choice(name=name[:-3],value=name[:-3]) for name,i in skekcommands.__dict__.items() if inspect.iscoroutinefunction(i) and callable and i.__name__[0] != "_"])
async def help(ctx,command:str|None):
    await helpCMD(ctx,command)


def main():
    client.run(os.environ.get("TOKEN_SKESTBOT" if isTest else "TOKEN_SKEKBOT"))

if __name__ == "__main__":
    main()
