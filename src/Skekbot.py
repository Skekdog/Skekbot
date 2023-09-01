from discord import Client,Intents,Message,Interaction,HTTPException,NotFound,Forbidden,Attachment,AppCommandType,Object,ChannelType
from discord.app_commands import CommandTree,Choice,describe,choices,Group,commands,AppCommandGroup,Range

from discord.utils import _ColourFormatter,MISSING
from logging import getLogger,StreamHandler,INFO

from re import findall
from time import time as time_s
from asyncio import sleep as asleep
from os import environ,chdir
from os.path import dirname,abspath

current_dir = dirname(abspath(__file__))
chdir(current_dir+"/..")

from Commands import *
from Constants import *
from Utils import *

lastFlavour = {} # // To prevent chat flooding when no slow mode
                 # // Format: {channelId: {lastDad: timestamp, lastWhatsUp: timestamp, etc: etc.}}
                 # // If relevant timestamp is <Cooldown seconds ago, Skekbot ignores it. Other flavours can still be sent.
def checkFlavour(id:int,flavour:str,cooldown:int) -> bool: return time_s()-cooldown>lastFlavour.setdefault(id,{}).get(flavour,0)

# // Constants. Easier to define these here rather than Constants.py
UPDATE_FILE = "/home/admin/Documents/Skekbot/update.txt"
IS_TEST = False

# // Intents
intents = Intents.none()
intents.message_content = True # // For What If and dad and some other things
intents.messages = True # // Same thing
intents.guilds = True # // The docs said it's a good idea to keep this enabled so...
intents.members = True # // So that we can know people's names and remove unwelcome people
intents.guild_reactions = True # // We don't need to know about reactions in DMs, for Reaction Roles

client = Client(intents=intents)
tree = CommandTree(client)
command = tree.command

sh = StreamHandler()
sh.setFormatter(_ColourFormatter())
logger = getLogger("skekbot")
logger.addHandler(sh)
logger.setLevel(INFO)

@client.event
async def on_ready():
    logger.info("Readied!")
    await tree.sync()
    logger.info("Global tree synchronised")
    while True:
        await asleep(5)
        try:
            with open(UPDATE_FILE,"r+") as f:
                msg = f.read()
                if not msg: raise AssertionError()
                if msg.split("\n")[0].split("=")[1].strip()!="False": raise AssertionError() # // To exit the context manager early
                msg = msg[msg.find("\n")+1:]
                f.seek(0)
                f.truncate(0)
                f.write("announced=True\n"+msg)
                for i in readFromKey(D_SS,"announcementchannels"):
                    if (not i) or (i == BLANK): continue
                    chan = client.get_channel(int(i))
                    if not chan: chan = await client.fetch_channel(int(i))
                    if not chan: continue
                    embed = SuccessEmbed("Skekbot Announcement",msg)
                    embed.set_author(name="Skekbot",icon_url="https://cdn.discordapp.com/avatars/1054474727642628136/8e55a5b1d22492c78d167ba26b5f4e04.webp?size=128") #// Skekbot pfp
                    await chan.send(embed=embed)
        except AssertionError: pass

@client.event
async def on_message(msg:Message):
    author = msg.author
    aId = author.id
    if aId in BOT_IDS: return # // Ignore if author is Skekbot or Skestbot. Otherwise we get two dads having the time of their life.

    channel = msg.channel
    cId = channel.id
    Content = msg.content
    content = msg.content.lower()
    ref = msg.reference

    # // Ignore everything else if this is a message in a /ask thread
    if channel.type == ChannelType.public_thread:
        sm = channel.starter_message
        msgs = [i async for i in channel.history(limit=None,oldest_first=True)]
        if not sm: sm = msgs[1]
        if sm and (sm.author.id in BOT_IDS) and checkFlavour(cId,"ask",5):
            try:
                send = msg.reply
                data = await fetch(sm.embeds[0].thumbnail.url,[TEXT_DF,TEXT_DF_CMD_RT],send)
                if not data: return
                data = decodeBotBin(data)
                if data["userid"] == aId:
                    lastFlavour[cId]["ask"] = time_s()
                    embed = SuccessEmbed(Content[:255],"Generating a response...")
                    rep = await send(embed=embed)
                    async def update(content):
                        embed.description = content
                        await rep.edit(embed=embed)
                    res,file,view = await ChatGPT(author,edit=update,chatOverride=[{"role":"system","content":getPersonalityById(data["personality"])}]+[
                        {"role":("user" if not (i.author.id in BOT_IDS) else "assistant"),"content":(i.content if not (i.author.id in BOT_IDS) else i.embeds[0].description)} for i in msgs[1:]
                    ])
                    embed.description = res
                    embed.set_thumbnail(url=DATA_ATTACHMENT)
                    return await rep.edit(embed=embed,attachments=[file],view=view)
            except: return

    replyText = BLANK
    if checkFlavour(cId,"dad",5):
        word = getStringAfterWord(content,DAD_TRIGGERS,["i am"],ARTICLES)
        if word != BLANK:
            try:
                word = word[:50].strip().capitalize().replace("@","@​") # // The generally accepted longest word is 45 letters. No need for much more
                replyText += f"Hi {word}, I'm dad!"
            except IndexError: # // Out of bounds
                pass
            lastFlavour[cId]["dad"] = time_s()
    if checkFlavour(cId,"whats",5):
        for i in WHAT_TRIGGERS:
            if i in content:
                replyText += ("\nAnd i" if replyText != BLANK else "I") + "t's the sky, probably."
                lastFlavour[cId]["whats"] = time_s()
                break

    replied = False
    if checkFlavour(cId,"whatif",10):
        bwiI,wiI = content.find("but what if"),content.find("what if")
        if ((bwiI != -1 and ref) or (wiI != -1)):
            lastFlavour[cId]["whatif"] = time_s()
            prompt = BLANK
            if bwiI != -1:
                # // Create a scenario based on previous message and what comes after "but what if" in this message
                # // But what if requires a reply
                # // Find replied message in cache, fetch it otherwise
                if ref:
                    for i in client.cached_messages:
                        if i.id == ref.message_id:
                            ref = i
                            break
                    if not isinstance(ref,Message):
                        ref = await channel.fetch_message(ref.message_id)

                    if isinstance(ref,Message):
                        # // We got the original message
                        refContent = ref.embeds[0].description if ref.embeds else ref.content
                        prompt = refContent[-500:]+" "+Content[bwiI:100] # // We should include "but what if" in the prompt. The but part should be short. Original context is important.

            elif wiI != -1:
                # // Create a scenario based on what comes after "what if" in this message
                prompt = (Content[wiI+7:])[:100] # // "what if" takes 7 chars

            if prompt != BLANK:
                
                embed = SuccessEmbed(prompt[:255],"Generating an outcome...")
                rep = await msg.reply(content=replyText,embed=embed)
                replied = True

                async def update(content:str):
                    embed.description = content
                    await rep.edit(embed=embed)

                res,file,view = await ChatGPT(author,
                    prompt=prompt+" Remember this all just for fun start in middle of action dont explain story"+(BLANK if randint(0,1) == 1 else " have tragic end"),
                    # // I would use randint *is* 1 but that gives an unsuppressable SyntaxWarning (I guess that is triggered at compilation)
                    edit=update,
                    personality=None,
                    max_tokens=1000, # // I'm very generous
                )
                embed.description = res
                embed.set_thumbnail(url=DATA_ATTACHMENT)
                await rep.edit(embed=embed,attachments=[file],view=view)

    if not replied and replyText != BLANK: await msg.reply(content=replyText,mention_author=False)

@client.event
async def on_member_join(member:Member):
    if member.id in UNWELCOMES: member.ban(reason="You are not welcome here.")

@client.event
# // The documentation is useless, instead we have to use the so-called "low-level" function for persistent buttons
async def on_interaction(ctx:Interaction):
    cid = ctx.data.get("custom_id",None)
    if not cid: return # // i.e this is a slash command and not a button

    send = ctx.response.send_message
    cid = cid.split("_")
    act = cid[0]
    if act == "comment": return await send(embed=INVALID_INTERACTION,ephemeral=True)

    msg,user = ctx.message,ctx.user

    if act == "regenerate":
        try: embed,comps,num = msg.embeds[0],msg.components,int(cid[2])
        except (IndexError,AttributeError,ValueError): return await send(embed=REGEN_FAILED,ephemeral=True)
        try: data = embed.thumbnail.url
        except AttributeError: return await send(embed=REGEN_FAILED,ephemeral=True)
        data = await fetch(data,[TEXT_DF,TEXT_DF_CMD_RT],send)
        if not data: return
        data = decodeBotBin(data)
        cf = checkFlavour(ctx.channel.id,"ask",10)
        if not cf: return await send(embed=REGEN_COOLDOWN,ephemeral=True)
        if data["userid"] == user.id:
            lastFlavour[ctx.channel.id]["ask"] = time_s()
            embed = SuccessEmbed(embed.title[:255],GENERATING_RESPONSE)
            await send(embed=embed)
            rep = await ctx.original_response()
            async def update(content):
                embed.description = content
                await rep.edit(embed=embed)
            res,file,view = await ChatGPT(user,embed.title,edit=update,personality=getPersonalityById(data["personality"],name=True))
            embed.description = res
            embed.set_thumbnail(url=DATA_ATTACHMENT)
            return await rep.edit(embed=embed,attachments=[file],view=view)
        
    elif act == "rps" or act == "nc":
        # // This used to be incredibly unreadable, and I had some comment going all like "this stinks here's what it does". Next time, make the code readable, silly
        m = [int(i) for i in findall(RE_USER_MENTION,msg.content) if i != BLANK]
        if len(m) != 2: return await send(embed=NO_PERMISSION,ephemeral=True) # // When game ends, we have one mention for the winner. Other mentions are replaced with username
        pid,pid2 = m[0],m[1] # // P(layer)ID

        if user.id != pid: return await send(embed=NO_PERMISSION,ephemeral=True) # // Not your turn

        plr,plr2 = client.get_user(pid),client.get_user(pid2) # // Try find them in cache
        if not plr: plr = await client.fetch_user(pid) # // Couldn't find in cache, pester Discord
        if not plr2: plr2 = await client.fetch_user(pid2) # // Couldn't find in cache, pester Discord
        if not plr or not plr2: return await send(embed=NO_PERMISSION,ephemeral=True) # // Who knows what's going on? I don't

        isBot = pid2 in BOT_IDS # // Remember that bot moves are done at the same time, so this function only runs when the human moves

        plrName,plr2Name = plr.display_name,plr2.display_name

        if act == "rps": # // There is an exception for rps, because you shouldn't know your opponent's move and it ends in 1 turn
            plr1Choice,plr2Choice = cid[1].capitalize(),cid[2].capitalize() # // Remember, plr2 is the person whose turn it currently isn't

            if isBot: plr2Choice = RPS_CHOICES[randint(0,2)] # // Boohoo how unoptimised ;( ITS GOING TO HAVE A HALF SECOND DELAY CONTACTING DISCORD, 1 PICOMICRONANOSECOND DOESNT MATTER!!!!!
            elif cid[2] == BLANK: return await send(f"<@{pid2}>, you have been challenged by <@{pid}> to a game of Rock, Paper, Scissors!",view=RpsView(plr1Choice))

            result = evalRps(plr1Choice,plr2Choice)
            winner = plrName if result == plr1Choice else plr2Name if result == plr2Choice else NOBODY
            longestName = plrName if len(plrName) > len(plr2Name) else plr2Name if len(plr2Name) > len(NOBODY) else NOBODY
            
            return await send(content=f'{padSpoiler(plrName,longestName)} chose {monoSpoiler(padSpoiler(plr1Choice,SCISSORS))}.\n {padSpoiler(plr2Name,longestName)} chose {monoSpoiler(padSpoiler(plr2Choice,SCISSORS))}.\n\n{monoSpoiler(padSpoiler(winner,longestName))} wins!',view=MISSING)
        
        if act == "nc":
            pass

    elif (act == "download") or (act == "variate"):
        try: embed,comps,num = msg.embeds[0],msg.components,int(cid[2])
        except (IndexError,AttributeError,ValueError): return await send(embed=DOWNLOAD_FAILED,ephemeral=True)
        
        img = embed.image
        if not img: return await send(embed=DOWNLOAD_FAILED,ephemeral=True)
        
        url = img.url

        send = ctx.followup.send
        if act == "download": await ctx.response.defer(ephemeral=True)
        else: await ctx.response.defer(thinking=True)

        cont = await fetch(url,[TEXT_DF,"Failed to download the base image. Try again later."],send)
        
        count = 0
        # // Count how many images there are
        for i in comps[0].children:
            if getattr(i,"custom_id",BLANK).startswith("download_image_"): count += 1

        area,h = None,img.height
        if count < 4:
            s = (num-1)*h+(STITCHBORDERPX*(num-1))
            area = (s,0,s+h,h,)
        else:
            h = ceil((h-STITCHBORDERPX)/2)
            rem = (num-1)%2
            s = (rem*h)+(rem*STITCHBORDERPX)
            first = (num/2 <= 1)
            area = (s,0 if first else h+(STITCHBORDERPX if not first else 0),s+h,h if first else (h*2)+(STITCHBORDERPX if not first else 0))

        data = BytesIO()
        img = Image.open(BytesIO(cont))
        img.crop(area).save(data,format="PNG")
        data.seek(0)
        img.close()
        
        if act == "download":
            try:
                embed = SuccessEmbed("Download Requested",f"Requested download of image {num} from [here]({url}). Enjoy!")
                embed.set_image(url="attachment://image.png")
                await user.send(file=File(data,filename="image.png"),embed=embed)
            except HTTPException as e:
                logger.error("Error sending DM: "+str(e)+str(e.args))
                embed = DOWNLOAD_FAILED_DM
                await send(ephemeral=True,embed=embed)
            return data.close()
        else:
            embed,file,view = await Imagine(user,toPNG(data.read()),1,True,True)
            embed.title = "Variation Completed"
            embed.description = f"Variation of image {num} from [here]({url}) completed. Enjoy!"
            await ctx.followup.send(file=file,embed=embed,view=view)
        data.close()

groups = []
# // We also need CharacterAI
askTree = Group(name="ask",description="Chat with AI models.",extras={"category":"OpenAI"})
groups.append(askTree)
@askTree.command(name="gpt",description="Chat with OpenAI's ChatGPT model.",extras={"category":"OpenAI"})
@describe(prompt="the text prompt from which to generate a response.",
            personality="the personality of the AI.")
@choices(personality=[Choice(name=i.title(),value=i) for i in PERSONALITIES if i]) # // "if i" accounts for the None option for no system message
async def ask_gpt(ctx:Interaction,prompt:str,personality:str="balanced"):
    if ctx.channel.type in [ChannelType.public_thread,ChannelType.private_thread,ChannelType.forum,ChannelType.news_thread]: return await ctx.response.send_message(embed=NO_THREAD_CMD,ephemeral=True)
    await ctx.response.defer(thinking=True)
    embed = SuccessEmbed(f'{personality.title()}: {prompt[:255]}',"Generating a response...")
    msg = await ctx.followup.send(embed=THREAD_CREATED,wait=True)
    thread = await ctx.channel.create_thread(name=prompt[:25],message=Object(msg.id))
    
    msg = await thread.send(embed=embed)
    async def update(content,file=None):
        embed.description = content
        await msg.edit(embed=embed,attachments=[file] if file else [])
        
    res,file,view = await ChatGPT(ctx.user,prompt,personality,update)
    embed.set_thumbnail(url=DATA_ATTACHMENT)
    embed.description = res
    await msg.edit(embed=embed,attachments=[file],view=view)
tree.add_command(askTree)

@command(name="transcribe",description="$$ transcribe a voice message into English, using OpenAI's Whisper.",extras={"category":"OpenAI","desc":"\nVoice messages in English will usually be more accurate. The language will attempt to be auto-detected, but sometimes this won't work.\nThis will work for any message where an ogg audio file is the first attachment."})
@describe(message="the link to the voice message. English messages tend to be more accurate.")
async def transcribe(ctx:Interaction,message:Range[str,15,100]):
    message = message.lower()
    lnk = message.split("/")
    # // Technically, we can first try looking through cached messages if an ID was sent. But then, fails will be inconsistent.
    if lnk == message or len(lnk) < 2: return await ctx.response.send_message(embed=INVALID_MESSAGE_LINK,ephemeral=True)
    msg = None
    for i in client.cached_messages:
        if i.id == lnk[-1]:
            msg = i
            break
    if not msg: msg = await (client.get_partial_messageable(lnk[-2])).fetch_message(lnk[-1])
    if not msg: return await ctx.response.send_message(embed=INVALID_MESSAGE_LINK,ephemeral=True)

    try: file=msg.attachments[0]; assert file.content_type.split("/")[0]=="audio"
    except (IndexError,AssertionError,AttributeError): return await ctx.response.send_message(embed=INVALID_VOICE_MESSAGE,ephemeral=True)

    data = await fetch(file.url,["Download Failed.","Failed to download audio data. Try again later."],ctx.response.send_message)
    if not data: return

    await ctx.response.defer(thinking=True)
    text = await Transcribe(data)
    if type(text) != str: return await ctx.followup.send(embed=text,ephemeral=True)
    await ctx.followup.send(embed=SuccessEmbed("Transcription Completed.",(f"`{msg.author.display_name}:` {text}")[:4096]))

@command(name="imagine",description="$$$ Generate images based off of a prompt, using OpenAI's DALLE-2 model.",extras={"category":"OpenAI"})
@describe(prompt="the text prompt from which to generate images.",
          amount="$⇈ amount of images to generate. Each image costs credits.",
          high_res="$↟ whether to generate images in 1024x1024 pixels.")
@choices(amount=[Choice(name=str(i+1),value=i+1) for i in range(4)])
async def imagine(ctx:Interaction,prompt:str,amount:int=1,high_res:bool=False):
    await ctx.response.defer(thinking=True)
    embed,file,view = await Imagine(ctx.user,prompt,amount,high_res)
    await ctx.followup.send(embed=embed,file=file,view=view)

@command(name="variations",description="$$$ Generate variations of an already existing square image, using OpenAI's DALLE-2 model.",extras={"category":"OpenAI","desc":"\nVisit [Pillow Docs](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) for a full list of supported formats. The format must be readable."})
@describe(image="the image to create variations of. Preferrably square and must be <4MB. Be aware this will be publicly accessible.",
          amount="$⇈ amount of variations to create. Each variation costs credits.",
          high_res="$↟ whether to create variations in 1024x1024 pixels.")
@choices(amount=[Choice(name=str(i+1),value=i+1) for i in range(4)])
async def variations(ctx:Interaction,image:Attachment,amount:int=1,high_res:bool=False):
    await ctx.response.defer(thinking=True)
    embed,file,view = await Imagine(ctx.user,toPNG(await image.read()),amount,high_res,True)
    embed.title = "Variation Completed"
    embed.description = "Variation"+("s" if amount > 1 else BLANK)+f" of [uploaded image]({image.url}) completed. Enjoy!"
    await ctx.followup.send(file=file,embed=embed,view=view)

def padSpoiler(choice,longest): return choice+(" "*abs(len(longest)-len(choice)))
def monoSpoiler(msg): return "||`"+msg+"`||"

@command(name="coin_flip",description="Great for making a bet and regretting it immediately afterwards.",extras={"category":"Other"})
async def coin_flip(ctx:Interaction): await ctx.response.send_message(monoSpoiler("Heads!" if randint(0,1)==1 else "Tails!"))

def evalRps(p1,p2):
    if p1 == p2: return False
    if p1 == ROCK: return p2 if p2 == PAPER else p1
    if p1 == PAPER: return p2 if p2 == SCISSORS else p1
    if p1 == SCISSORS: return p2 if p2 == ROCK else p1

@command(name="rock_paper_scissors",description="Rock, Paper, Scissors! - the only way to win an argument.",extras={"category":"Games"})
@describe(versus="Who to play against. You can leave it blank if you want to play against Skekbot.")
async def rock_paper_scissors(ctx:Interaction,versus:Member): await ctx.response.send_message(content=f"{ctx.user.mention}, make your move against {versus.mention}.",view=RpsView(),ephemeral=True)
# // Everything is handled in on_interaction

@command(name="noughts_and_crosses",description="(Tic Tac Toe)",extras={"category":"Games"})
async def noughts_and_crosses(ctx:Interaction,versus:Member): await ctx.response.send_message(content=f"{ctx.user.mention}, make your move against {versus.mention}.\n"+NC_BOARD,view=NCView())

@command(name="about",description="Find out about Skekbot here.")
async def about(ctx:Interaction): await ctx.response.send_message(embed=ABOUT_EMBED)

local_cmds,cmd_cache,help_overview = tree.get_commands(type=AppCommandType.chat_input),[],None
helpChoices = []
for cmd in local_cmds.copy():
    cn = cmd.name
    childs = getattr(cmd,"commands",[])
    if len(childs) > 0:
        for v in childs: helpChoices.append(Choice(name=cn+" "+v.name,value=v.name)),local_cmds.append(v)
        continue
    helpChoices.append(Choice(name=cn,value=cn))
@command(name="help",description="Get help with Skekbot.")
@describe(command="Specific command to get more information on.")
@choices(command=helpChoices) # // This does mean help wont appear. meh
async def help(ctx:Interaction,command:str=None):
    if command:
        global cmd_cache
        if not cmd_cache:
            allCmds = await tree.fetch_commands()
            for i in allCmds:
                for v in i.options:
                    if type(v) != AppCommandGroup: continue
                    allCmds.append(v)
            cmd_cache = allCmds
        cmd,local_cmd = next((obj for obj in cmd_cache if obj.name == command),None),tree.get_command(command)
        if not local_cmd:
            # // Look for it in a group
            for group in groups:
                for i in group.commands:
                    if i.name == command:
                        local_cmd = i
                        break 
        if not cmd or not local_cmd: return await ctx.response.send_message(embed=FailEmbed("Unknown command: "+command,f"Failed to fetch {('local' if not local_cmd else 'remote')} help for command."))
        
        extras = local_cmd.extras
        doc = f'### Description:\n**Category: {extras.get("category","None")}**\n{CMD_CATS[extras.get("category","None")]}\n\n{cmd.description}{extras.get("desc",BLANK)}'
        params = local_cmd.parameters
        if len(params) > 0: doc += "\n### Parameters:\n"
        for i in params:
            doc += f"`{i.name}:` {i.description}\n"
        return await ctx.response.send_message(embed=SuccessEmbed(f'{cmd.mention} Help',doc))
    global help_overview
    if help_overview: await ctx.response.send_message(embed=help_overview)
    else:
        cat_docs = {i:f'\n### {i}:\n{CMD_CATS[i]}' for i in CMD_CATS if i != "None"}
        for i in local_cmds:
            if type(i) != commands.Command: continue
            cat_docs[i.extras["category"]] += f'\n\n**{i.qualified_name}:**\n{i.description}'
        doc = BLANK
        for _,v in cat_docs.items():
            doc += v
        help_overview = SuccessEmbed("Command List","You can specify the `command` parameter of </help:1145022212290658434> to get detailed information on a command.\n"+doc)
        await ctx.response.send_message(embed=help_overview)

def main():
    client.run(environ.get("TOKEN_SKESTBOT" if IS_TEST else "TOKEN_SKEKBOT"))

if __name__ == "__main__":
    main()