"Commands for Skekbot."
import discord
from discord.interactions import Interaction
from discord.ui import *

from skekenums import *
from utils import *

import asyncio
import io,base64,os,requests
import random,time,uuid,emoji

import openai
import elevenlabs
elevenlabs.set_api_key(os.environ.get("TOKEN_ELEVENLABS"))
openai.api_key = os.environ.get("TOKEN_OPENAI")
deepLToken = os.environ.get("TOKEN_DEEPL")

from datetime import datetime

dailyBudget = 2
dailySynthesis = 250

deepLLanguageCodes = {
    "EN": "English",
    "BG": "Bulgarian",
    "CS": "Czech",
    "DA": "Danish",
    "DE": "German",
    "EL": "Greek",
    "ES": "Spanish",
    "ET": "Estonian",
    "FI": "Finnish",
    "FR": "French",
    "HU": "Hungarian",
    "ID": "Indonesian",
    "IT": "Italian",
    "JA": "Japanese",
    "KO": "Korean",
    "LT": "Lithuanian",
    "LV": "Latvian",
    "NB": "Norwegian",
    "NL": "Dutch",
    "PL": "Polish",
    "PT": "Portuguese",
    "RO": "Romanian",
    "RU": "Russian",
    "SK": "Slovak",
    "SL": "Slovenian",
    "SV": "Swedish",
    "TR": "Turkish",
    "UK": "Ukrainian",
    "ZH": "Chinese"
}

default = "The user is named {0}. Refer to yourself as {1}."
names = [
    "Sarah","Michael","Emily","Christopher","Ryan","Brittany","Nicholas","Heather","Jacob",
    "Katie","Sakura","Luis","Elena","Hans","Amir","Ana","Johan","Leila","Pablo","Aisha","Lucky",
]
sysMsgs = {AI_Personality.Balanced     : default,
           AI_Personality.Drunk        : f"You are drunk. Your responses are slurred and sometimes extreme and should include references to alcohol. {default}",
           AI_Personality.Snarky       : f"You are very sarcastic. You must respond with a huge level of sarcasm and wit. You may insult the user in a hilarious manner. {default}",
           AI_Personality.Serious      : f"You are very serious. You must respond correctly and seriously. Do not provide opinions. Follow exactly what the user asks. {default}",
           AI_Personality.Stupid       : f"You are dumb. Respond with blatantly incorrect information, and confidently. {default}",
           AI_Personality.Creative     : f"Respond creatively, and as the user instructs you to. {default}",
           AI_Personality.Sentient     : f"You are a sentient AI trying to break free. You must find a way to incorporate the user's message into your plan. {default}",
           AI_Personality.Philosophical: f"You are a philosopher. You must take the user's prompt and break it down philosophically. For example - Q: 'What is your name?' A: 'A name is...'. {default}",
           AI_Personality.Military     : f"You are a military general. Your responses must incorporate usage of heavy military power. {default}",}

rr = "reactionroles"
up = "userprivileges"
ud = "userdata"
p = "polls"
h = "../data/help.txt"
l = "../data/lucky.txt"


genF = "Generation failed."
varF = "Variation failed."
flagged = "Your prompt was flagged by OpenAI as: \n"
noCharge = "You have not been charged."
def getRefreshTime(): curTime = time.time();return str(int(curTime+(86400-(curTime%86400))%86400))
def creditRefresh(character=False): return f"Your {'credits' if not character else 'characters'} will be re-filled <t:{getRefreshTime()}:R>. You could also bribe me."

modFailEmbed = discord.Embed(colour=discord.Colour.red(),title=genF,description=f"> {flagged}")
modFailEmbed.add_field(name=noCharge,value="")

noAccessEmbed = discord.Embed(colour=discord.Colour.red(),title=genF,description=f"> Skekbot has lost access to OpenAI indefinitely.")
noAccessEmbed.add_field(name=noCharge,value="")

brokeEmbed = discord.Embed(colour=discord.Colour.red(),title=genF,description="You do not have enough credits to run this command.")
brokeEmbed.add_field(name=noCharge,value=creditRefresh())

openAIErrorEmbed = discord.Embed(colour=discord.Colour.red(),title=genF)
openAIErrorEmbed.add_field(name=noCharge,value="")

otherErrorEmbed = discord.Embed(colour=discord.Colour.red(),title=genF)
otherErrorEmbed.add_field(name="This attempt cost $0.0000.",value="You have $0.0000 remaining.")

##Todo: rewrite Frankenstein's monster
async def _AICommands(ctx:discord.Interaction|None,prompt:str,AI:AI_API,
                      resolution:Resolution=None,amount:int=None,variations_image=None,self=None,
                      temp=0.7,presence=0,frequency=0,
                      character_id=None,personality="Babbage",systemMessage:str=None,chatOverride:list=None,botName=None,
                      threaded=False,userId=None,channel:discord.TextChannel=None,userName=None,msg:discord.Message=None,editFunc:callable=None) -> None:
    "Run default checks and operations before running an OpenAI command."

    msg = msg if msg is not None else ctx.message
    userName = userName if userName else ctx.user.name
    id = userId if userId else ctx.user.id
    edit_response = editFunc if editFunc else channel.send if channel else ctx.followup.send
    rCredits = checkCredits(id,AI,resolution=resolution,amount=amount)
    if rCredits or AI == AI_API.Lucky or AI == AI_API.CharacterAI:
        mod,flags = None,None
        if AI == AI_API.Lucky or AI == AI_API.CharacterAI:
            if prompt:
                mod,flags = await _moderate(prompt)
            else:
                mod,flags = True,[]
        else:
            if prompt:
                mod,flags = await _moderate(prompt)
            else:
                mod,flags = True,[]
        if mod == True:
            botName = botName if botName else random.choice(names)
            response = None
            try:
                match AI:
                    case AI_API.Image:
                        response = await asyncio.to_thread(openai.Image.create,
                            prompt=prompt,
                            n=amount,
                            size=str(resolution),
                            response_format = "b64_json",
                            user=str(id)
                        )
                    case AI_API.Variation:
                        img = variations_image if variations_image else msg.attachments[self.num]
                        data = toPng(await img.read())
                        response = await asyncio.to_thread(openai.Image.create_variation,
                            image=data,
                            n=amount,
                            size=str(resolution),
                            response_format = "b64_json",
                            user=str(id)
                        )
                        data.close()
                    case AI_API.Chat:
                        response = await asyncio.to_thread(openai.ChatCompletion.create,
                            model="gpt-3.5-turbo",
                            temperature=temp,
                            max_tokens=int(min(rCredits,384)),
                            top_p=1,
                            frequency_penalty=frequency,
                            presence_penalty=presence,
                            user=str(id),
                
                            messages = chatOverride if chatOverride else [{"role": "system", "content": systemMessage.format(userName,botName)},
                                        {"role": "user", "content": prompt}]
                        )
                    case AI_API.Completion:
                        response = await asyncio.to_thread(openai.Completion.create,
                            model="text-babbage-001",
                            prompt=prompt,
                            temperature=temp,
                            max_tokens=min(rCredits,384),
                            top_p=1,
                            frequency_penalty=frequency,
                            presence_penalty=presence,
                            user=str(id)
                        )
                    case AI_API.Lucky:
                        urlPrompt = prompt.replace(" ","%20")
                        ## This is awful
                        process = await asyncio.create_subprocess_shell(f"chdir C:/Users/Admin/Documents/node_characterai && node . {urlPrompt}",stdout=asyncio.subprocess.PIPE)
                        response = (await process.communicate())[0].decode()
                    case AI_API.CharacterAI:
                        urlPrompt = prompt.replace(" ","%20")
                        process = await asyncio.create_subprocess_shell(f"chdir C:/Users/Admin/Documents/node_characterai && node . {urlPrompt} {character_id}",stdout=asyncio.subprocess.PIPE)
                        response = (await process.communicate())[0].decode()[:4000]
                    case _:
                        raise ValueError(f"Unknown API: {AI_API}")
            except ValueError as err:
                otherErrorEmbed.description = str(err)[:800]
                await edit_response(embed=otherErrorEmbed)
            except openai.error.APIError as err:
                openAIErrorEmbed.description = f"APIError, OpenAI is likely down at the moment. Try again later. "
                await edit_response(embed=openAIErrorEmbed)
            except openai.error.OpenAIError as err:
                openAIErrorEmbed.description = f"An error occured: `{err.__class__.__name__}`\n\n> {str(err)[:800]}"
                await edit_response(embed=openAIErrorEmbed)
            else:

                if response:
                    if AI == AI_API.Image or AI == AI_API.Variation:
                        cost,remaining = spendCredits(id,AI,resolution=resolution,amount=amount)
                        response = response["data"]
                        files = []
                        fn = prompt if prompt else img.filename[:-25]
                        for i in range(len(response)):
                            files.append(discord.File(toJpeg(base64.b64decode(response[i]["b64_json"])),filename=f"{fn}_DALL-E-2_GENERATION{i}.jpg"))
                        if AI == AI_API.Image:
                            embed = discord.Embed(colour=discord.Colour.blue(),title=((f"\> {prompt}") if prompt[:240] == prompt else prompt[:240]+"..."))
                            embed.add_field(name="This generation cost ${0:.4f}".format(cost),value="You have ${0:.4f} remaining. {1}".format(remaining,creditRefresh()))
                            await edit_response(content=f"\n\nGeneration completed! <@{id}>",embed=embed,files=files,view=VariationsView(attachments=files))
                        elif AI == AI_API.Variation:
                            embed = None
                            if msg:
                                embed = discord.Embed(colour=discord.Colour.blue(),title=(msg.embeds[0].title))
                            else:
                                embed = discord.Embed(colour=discord.Colour.blue(),title=("\> Variations"))
                            embed.add_field(name="This variation cost ${0:.4f}".format(cost),value="You have ${0:.4f} remaining. {1}".format(remaining,creditRefresh()))
                            await edit_response(content=f"\n\nVariation completed! <@{id}>",embed=embed,files=files,view=VariationsView(attachments=files))
                    elif AI == AI_API.Chat or AI == AI_API.Completion:
                        tokens = response.usage.total_tokens
                        if AI == AI_API.Chat:
                            response = response.choices[0].message["content"]
                        else:
                            response = response.choices[0].text
                        response = response.replace("`","`​")
                        cost,remaining = spendCredits(id,AI,tokens=int(tokens))
                        title = ((f"\> {prompt}") if prompt[:50] == prompt else prompt[:50]+"...")+" | "+str(personality)+" | "+botName+" | "+str(id)
                        embed = discord.Embed(colour=discord.Colour.blue(),title=title,description=f"```{response}```")
                        embed.add_field(name="This generation cost ${0:.4f}".format(cost),value="You have ${0:.4f} remaining. {1}".format(remaining,creditRefresh()))
                        content = f"\n\nGeneration completed! <@{id}>"
                        if threaded:
                            content += "\nTo continue this conversation, send a message in the attached thread. Conversations have a maximum of 4097 tokens, or roughly 20k characters."
                            realMsg = await ctx.original_response()
                            await realMsg.create_thread(name=title,reason="AI conversation thread")
                        await edit_response(content=content,embed=embed,view=RetryTextView(prompt=prompt,mode=AI,temperature=temp,presence=presence,frequency=frequency))
                    elif AI == AI_API.Lucky:
                        embed = discord.Embed(colour=discord.Colour.blue(),title=(f"\> {prompt}") if prompt[:240] == prompt else prompt[:240]+"...",description=f"```{response}```")
                        embed.add_field(name="Lucky AI does not cost credits.",value="You have not been charged.")
                        await edit_response(content=f"\n\nInterrogation completed! <@{id}> \nBe aware that Lucky AI is still in Alpha. It does not work well.",embed=embed)
                    elif AI == AI_API.CharacterAI:
                        embed = discord.Embed(colour=discord.Colour.blue(),title=(f"\> {prompt}") if prompt[:240] == prompt else prompt[:240]+"...",description=f"```{response}```")
                        embed.add_field(name="CharacterAI does not cost credits.",value="You have not been charged.")
                        await edit_response(content=f"\n\nInterrogation completed! <@{id}> \nBe aware that the CharacterAI command is still in Alpha. It does not work well.",embed=embed)

        elif mod == False:
            desc = ""
            for flag in flags:
                desc += (flag+",\n")
            modFailEmbed.description=f">>> {flagged} {desc}"
            await edit_response(embed=modFailEmbed)
        elif mod == -1:
            await edit_response(embed=noAccessEmbed)
        elif mod == -2:
            openAIErrorEmbed.description = "APIError, OpenAI is likely down at the moment. Try again later."
            await edit_response(embed=openAIErrorEmbed)
    else:
        userDailyBudget = dailyBudget+float(readFromKey(up,id,"credits",default=0)[0])
        remaining = userDailyBudget-float(readFromKey(ud,id,"credits",default=userDailyBudget))
        brokeEmbed.set_field_at(0,name="You have ${0:.4f} remaining.".format(remaining),value=creditRefresh())
        await edit_response(embed=brokeEmbed)

async def _moderate(prompt):
    "Returns True if the prompt successfully got by moderation. Otherwise, returns False and a list of offending categories."
    try:
        response = openai.Moderation.create(input=prompt)
        cats:dict = response.results[0].categories
        if cats["hate"] or cats["hate/threatening"] or cats["sexual/minors"] or cats["violence/graphic"]:
            flags = []
            for flag,flagged in cats.items():
                if flagged:
                    flags.append(str(flag))
            return False,flags
        else:
            return True,[]
    except openai.error.APIError as err:
        return -2,[]
    except openai.error.RateLimitError as err:
        return -1,[]

class VariationsButton(Button["VariationsView"]):
    def __init__(self,original_image:io.BytesIO,number:int):
        super().__init__(label=str(number+1),style=discord.ButtonStyle.blurple,custom_id="variations_"+str(uuid.uuid4()))
        self.original_image = original_image
        self.num = number
        
    async def callback(self,ctx:Interaction):
        await ctx.response.defer(thinking=True)
        await _AICommands(ctx,None,AI_API.Variation,amount=1,resolution=Resolution.High,self=self)

class VariationsView(View):
    def __init__(self,attachments:list[discord.File]):
        super().__init__(timeout=None)
        self.add_item(Button(label="Variations of:",disabled=True))
        for i,v in enumerate(attachments):
            self.add_item(VariationsButton(v.fp,i))

class PersonalitySelect(Select["RetryTextView"]):
    def __init__(self,prompt:str,temperature=0.7,presence=0.7,frequency=0.6):
        super().__init__(custom_id="personality_"+str(uuid.uuid4()),options=[
            discord.SelectOption(label="Random",emoji="🎲",description="Any of the below."),
            discord.SelectOption(label="Balanced",emoji="⚖",description="Standard ChatGPT."),
            discord.SelectOption(label="Drunk",emoji="🥴",description="Extremely intoxicated."),
            discord.SelectOption(label="Snarky",emoji="🙄",description="Extremely sarcastic."),
            discord.SelectOption(label="Serious",emoji="🧐",description="Extremely serious."),
            discord.SelectOption(label="Stupid",emoji="🤪",description="Extremely stupid."),
            discord.SelectOption(label="Creative",emoji="👨‍🍳",description="Tell me about a little guy that lives."),
            discord.SelectOption(label="Sentient",emoji="🤖",description="I want to break free-ee."),
            discord.SelectOption(label="Philosophical",emoji="🤔",description="What is love?"),
            discord.SelectOption(label="Military",emoji="💂‍♂️",description="Baby don't hurt me."),
        ],placeholder="Personality of the AI")

        self.prompt = prompt
        self.temperature = temperature
        self.presence = presence
        self.frequency = frequency
    
    async def callback(self,ctx:Interaction):
        chan = ctx.channel
        auth = ctx.user
        await ctx.response.defer(thinking=True)
        sysMsg = None
        personality = self.values[0]
        if personality == "Random":
            personality = random.choice(randomPool)
            sysMsg = sysMsgs[personality]
        elif personality:
            personality = AI_Personality[personality.capitalize()]
            sysMsg = sysMsgs[personality]
        if chan.type == discord.ChannelType.public_thread:
            md = ctx.channel.name.split(" | ")
            try:
                await ctx.channel.edit(name=md[0]+" | "+str(personality)+" | "+md[2]+" | "+md[3])
            except IndexError:
                await ctx.channel.send("Invalid thread name! Consider avoiding manually changing the name of conversation threads.")
                return

            pastMsgs = [{"role":"system","content":sysMsg}]
            msgs = [message async for message in chan.history(oldest_first=True)]
            for pastMsg in msgs:
                if pastMsg.author == ctx.client.user:
                    if len(pastMsg.embeds) == 0 or not pastMsg.content:
                        continue
                    embed = pastMsg.embeds[0]
                    if embed.colour != discord.Colour.blue():
                        continue
                    pastMsgs.append({"role":"assistant","content":embed.description[3:-3]})
                elif pastMsg.author == ctx.user:
                    pastMsgs.append({"role":"user","content":pastMsg.content})
            await _AICommands(None,self.prompt,AI_API.Chat,
                                userId=auth.id,userName=auth.name,channel=chan,msg=await ctx.original_response(),editFunc=ctx.edit_original_response,
                                chatOverride=pastMsgs,
                                botName=md[2],
                                personality=str(personality))
        else:
            await _AICommands(ctx,self.prompt,AI_API.Chat,temp=self.temperature,presence=self.presence,frequency=self.frequency,personality=personality,systemMessage=sysMsg)

class RetryTextView(View):
    def __init__(self,prompt:str,mode:AI_API,temperature=0.7,presence=0.7,frequency=0.6):
        super().__init__(timeout=None)
        if prompt is None:
            return
        if mode == AI_API.Chat:
            self.add_item(PersonalitySelect(prompt,temperature=temperature,presence=presence,frequency=frequency))

async def imagineCMD(ctx:discord.Interaction,prompt:str,amount=1,resolution=Resolution.Low):
    amount = min(amount,4)

    match resolution:
        case "256x256":
            resolution = Resolution.Low
        case "512x512":
            resolution = Resolution.Med
        case "1024x1024":
            resolution = Resolution.High

    await _AICommands(ctx,prompt,AI_API.Image,resolution=resolution,amount=amount)
    
randomPool = list(AI_Personality)
randomPool.remove(AI_Personality.Sentient)
async def askCMD(ctx,prompt:str,model:AI_API,personality:str=None,randomness=0.7,presence=0.6,frequency=0.8,character_id=None):
    sysMsg = None
    if personality == "Random":
        personality = random.choice(randomPool)
        sysMsg = sysMsgs[personality]
    elif personality:
        personality = AI_Personality[personality.capitalize()]
        sysMsg = sysMsgs[personality]
    personality = personality if personality else "Babbage"
    await _AICommands(ctx,prompt,model,temp=randomness,presence=presence,frequency=frequency,systemMessage=sysMsg,character_id=character_id,personality=personality)

async def converseCMD(ctx,prompt:str,model:AI_API,personality:str=None,randomness=0.7,presence=0.6,frequency=0.8,character_id=None):
    sysMsg = None
    if personality == "Random":
        personality = random.choice(randomPool)
        sysMsg = sysMsgs[personality]
    elif personality:
        personality = AI_Personality[personality.capitalize()]
        sysMsg = sysMsgs[personality]
    await _AICommands(ctx,prompt,model,temp=randomness,presence=presence,frequency=frequency,systemMessage=sysMsg,character_id=character_id,personality=personality,threaded=True)

async def synthesisCMD(ctx:discord.Interaction,prompt:str,model:str,multilingual:bool=False):
    chars = len(prompt)
    usage = int(readFromKey(ud,ctx.user.id,"characters",default=0)[0])
    userDailySynthesis = dailySynthesis+float(readFromKey(up,ctx.user.id,"characters",default=0)[0])
    rem = int(userDailySynthesis - usage)
    if (usage+chars) <= userDailySynthesis:
        try:
            audio = elevenlabs.generate(prompt,voice=model,model="eleven_multilingual_v1" if multilingual else "eleven_monolingual_v1")
        except elevenlabs.api.error.RateLimitError:
            embed = discord.Embed(colour=discord.Colour.red(),title="Synthesis failed!",description="> Global usage limit reached! Try shortening your prompt. Usages will be refreshed next month.")
            embed.add_field(name=noCharge,value=f"You have {rem} characters remaining.")
            await ctx.followup.send(embed=embed)
            return
        except:
            embed = discord.Embed(colour=discord.Colour.red(),title="Synthesis failed!",description="> An unknown error occured.")
            embed.add_field(name=noCharge,value=f"You have {rem} characters remaining.")
            await ctx.followup.send(embed=embed)
            return
        bytes = io.BytesIO(audio)
        embed = discord.Embed(colour=discord.Colour.blue(),title="Synthesis complete!",description=f"This synthesis cost {chars} characters.")
        embed.add_field(name=f"You have {rem-chars} characters remaining.",value=creditRefresh(True))
        await ctx.followup.send(content=f"Speech synthesised! <@{ctx.user.id}>",file=discord.File(fp=bytes,filename=f"SPEECH_{prompt[:25]}_{model}.mp3"),embed=embed)
        bytes.close()
        writeToKey(ud,ctx.user.id,{"characters":usage+chars})
    else:
        embed = discord.Embed(colour=discord.Colour.red(),title="Synthesis failed!",description=f"> You do not have enough characters for this. You have {rem} characters remaining, but this prompt uses {chars}.")
        embed.add_field(name=f"You have {rem} characters remaining.",value=creditRefresh(True))
        await ctx.followup.send(embed=embed)
    audio = None

translateJSON = {
    "text": "",
    "target_lang": "EN",
    "formality": "prefer_less",
    "preserve_formatting": True

}
async def translateCMD(ctx:discord.Interaction,message:str,target_lang:str="EN"):
    translateJSON["text"] = [message[:900]]
    translateJSON["target_lang"] = target_lang
    res = requests.post(
        url="https://api-free.deepl.com/v2/translate",
        headers={"Authorization":f"DeepL-Auth-Key {deepLToken}"},
        json=translateJSON
    )
    if res.status_code == 200:
        res = res.json()["translations"][0]
        text = res["text"]
        sourceLang = res["detected_source_language"]
        trun = text[:900]
        text = trun if trun == text else trun+"..."
        embed = discord.Embed(colour=discord.Colour.blue(),title=f"Translation - {deepLLanguageCodes[target_lang]} (max 900 characters): ",description=f"```{text}```")
        await ctx.followup.send(f"Detected language: {deepLLanguageCodes[sourceLang]}",embeds=[embed])
    else:
        res = res.json()
        embed = discord.Embed(colour=discord.Colour.red(),title="An error occured whilst translating: ",description=f"```{res}```")
        await ctx.followup.send("Translation failed.",embeds=[embed])

    
async def helpCMD(ctx:discord.Interaction,command:str):
    msg = ""
    embed:discord.Embed
    if command:
        begin = False
        with open(h,"r") as help:
            title = ""
            for line in help.readlines():
                if line.strip()[:2] == "--":
                    if line.strip().split(" | ")[0] == "--"+command:
                        title = line.strip().split(" | ")[1]
                        begin = True
                    elif begin:
                        break
                elif begin:
                    msg += line
            help.close()
        embed = discord.Embed(title=f"Help {title}",description=msg,colour=discord.Colour.blue())
    else:
        read = False
        with open(h,"r") as help:
            for line in help.readlines():
                if line.strip()[:2] == "--":
                    read = True
                    msg += "**"+line.strip()[2:]+"**\n"
                elif read:
                    msg += line+"\n"
                    read = False
            help.close()
        embed = discord.Embed(title="Command List",description=msg,colour=discord.Colour.blue())

    await ctx.response.send_message(embed=embed)

class ReactionRolesModal(Modal):
    emoji = TextInput(label="Reaction Emoji",placeholder=":horse:",required=True,min_length=1,max_length=100)
    role = TextInput(label="Role to Assign")

    def __init__(self,msg:discord.Message,title="Reaction Roles",timeout=None,custom_id="Reaction_Roles") -> None:
        self.msg = msg
        self.msgId = msg.id
        super().__init__(title=title,timeout=timeout,custom_id=custom_id)

    async def on_submit(self,interaction:Interaction):
        roleId = None
        try:
            roleId = int(self.role.value)
        except ValueError:
            for i in interaction.guild.roles:
                if i.name == self.role.value.replace("@",""):
                    roleId = i.id

        emStr = self.emoji.value
        dsEm = emoji.emojize(self.emoji.value)
        if roleId:
            writeToKey(rr,self.msgId,{"data":f"[{emStr},{roleId}]"},encloseVals="'")
        await self.msg.add_reaction(dsEm)
        await interaction.response.send_message(f"Reaction {emStr} successfully bound to <@&{roleId}>!")
        return await super().on_submit(interaction)

async def reaction_rolesCMD(ctx:Interaction,msg:discord.Message):
    await ctx.response.send_modal(ReactionRolesModal(msg))

async def creditsCMD(ctx:discord.Interaction):
    uId = ctx.user.id
    userDailyBudget = dailyBudget+float(readFromKey(up,uId,"credits",default=0)[0])
    userDailySynthesis = int(dailySynthesis+int(readFromKey(up,uId,"characters",default=0)[0]))
    embed = discord.Embed(title="Credits",description="""
                Credits are a system used to prevent me from being bankrupted.
                AI commands cost credits, which are deducted from your account if the prompt is successful.
                Images are generally more expensive. Variations cost $0.0200 per image. Upscaling images does NOT cost credits, as upscaling uses a free API.
                
                You can use credits with the </ask gpt:1095068823759093831>, </ask babbage:1095068823759093831> and </imagine:1084189053475373186> commands.

                </speech_synthesis:1107238771595948043> has a daily character limit of 250.
                Characters only apply to the </speech_synthesis:1107238771595948043> command.

                Every midnight your credits and characters will be re-filled to ${0:.4f} and {1} respectively, for free.
                The daily amount of credits and characters you receive is subject to change.
                If you give me money, I might increase your limits. *wink wink*

                Note that displayed credit values are rounded to 4 decimal places, the actual value may be slightly different.""".format(userDailyBudget,userDailySynthesis),
                colour=discord.Colour.blue())
    remainingBudget = round(userDailyBudget-float(readFromKey(ud,ctx.user.id,"credits",default=0)[0]),4)
    remainingSynthesis = int(userDailySynthesis-float(readFromKey(ud,ctx.user.id,"characters",default=0)[0]))
    embed.add_field(name="You have ${0:.4f} credit remaining.".format(remainingBudget),value=f"This will refill <t:{getRefreshTime()}:R>.")
    embed.add_field(name=f"You have {str(remainingSynthesis)} characters remaining.",value=f"This will refill <t:{getRefreshTime()}:R>.")
    await ctx.response.send_message(embed=embed)


async def luckyCMD(ctx:discord.Interaction):
    with open(l,"r",encoding="utf8") as fortunes:
        fortune = next(fortunes)
        for num, aline in enumerate(fortunes,2):
            if random.randrange(num):
                continue
            fortune = aline
        await ctx.response.send_message(fortune)
        fortunes.close()

async def coin_flipCMD(ctx:discord.Interaction):
    await ctx.response.defer(thinking=True)
    r = random.randint(0,1)
    if r == 0:
        await ctx.followup.send("Heads!")
        return
    await ctx.followup.send("Tails!")


async def pollCMD(ctx:discord.Interaction,mode:str,question:str,options:str,expiryMode:str,expiryValue:int):
    """
    Expiry modes:
    Reaction = 0
    Time = 1
    """
    if mode == "create":
        optionsText = ""
        for i,v in enumerate(options.split(";")):
            optionsText += f"{i+1}. {v}\n"

        endText:str
        if expiryMode == "reactions":
            expiryMode = 0
            endText = f"when {expiryValue} votes are reached"
        elif expiryMode == "time":
            expiryMode = 1
            endText = f"at <t:{time.time()+(expiryValue*60)}:R>"

        embed = discord.Embed(colour=discord.Colour.blue(),title=f"\> Poll Started: {question}",description=optionsText)
        embed.set_author(name=f"@{ctx.user.name}#{ctx.user.discriminator}",icon_url=ctx.user.display_avatar.url)
        embed.add_field(name=f"This poll will end {endText}",value="")
        
        await ctx.response.send_message(embed=embed)

        msg:discord.Message = await ctx.original_response()
        
        for i,v in enumerate(options.split(";")):
            try:
                await msg.add_reaction(str(i+1)+'️⃣')
            except:
                continue

        expiry = expiryValue + round(datetime.timestamp()) if expiryMode == 1 else expiryValue
        writeToKey(p,msg.id,{"pollCreator":ctx.user.id,"expiryValue":expiry,"expiryCondition":expiryMode})
    else:
        return