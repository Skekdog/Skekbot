from typing import Optional
from discord import Member,File,ButtonStyle
from discord.ui import View,Button

from os import environ
from asyncio import to_thread
from random import randint
from time import time_ns
from PIL import Image
from base64 import b64decode
from uuid import uuid4
from io import BytesIO
from math import ceil

from openai import ChatCompletion as ChatCompletion,Image as OpenAIImage,Audio as Audio
from openai.error import APIError,InvalidRequestError,Timeout,RateLimitError,APIConnectionError,InvalidRequestError,AuthenticationError,ServiceUnavailableError
import openai
openai.api_key = environ.get("TOKEN_OPENAI")

from Constants import *
from Utils import *

async def OpenAIErrors(func,**kwargs):
    try:
        response = await to_thread(func,**kwargs)
        return response
    except APIError:
        return ERR_OCCURRED+" on OpenAI's end. Check (OpenAI Status)[https://status.openai.com/]."
    except Timeout:
        return ERR_OCCURRED+" with Skekbot. Try again later."
    except RateLimitError as e:
        return "Skekbot is being rate-limited. Try again later."
    except APIConnectionError as e:
        return ERR_OCCURRED+" whilst connecting to OpenAI. Try again later."
    except InvalidRequestError as e:
        return ERR_OCCURRED+" on Skekbot's end. Please try again."
    except AuthenticationError as e:
        return ERR_OCCURRED+" whilst authenticating API access. Please watch for any updates from Skekbot on this matter."
    except ServiceUnavailableError as e:
        return ERR_OCCURRED+" on OpenAI's end. Please try again later."
    except BaseException as e:
        return str(e)
    
class CommentButton(Button):
    "A disabled and greyed out button to show a comment to the user."
    def __init__(self,comment:str,row:int):
        super().__init__(style=ButtonStyle.grey,label=comment,disabled=True,custom_id="comment_button_"+str(uuid4()),row=row)

class ImageView(View):
    def __init__(self,amount:int):
        super().__init__(timeout=None)
        
        self.add_item(CommentButton("Download:",0))
        self.add_item(CommentButton("Variations of:",1))
        for i in range(amount):
            self.add_item(Button(label=str(i+1),custom_id="download_image_"+str(i+1),row=0,style=ButtonStyle.green))
            self.add_item(Button(label=str(i+1),custom_id="variate_image_"+str(i+1),row=1,style=ButtonStyle.blurple))

class AskView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Generate Again!",custom_id="regenerate_ask_1"))

class RpsView(View):
    def __init__(self,choice=""): # // Choice="" represents player 1 making their choice
        super().__init__(timeout=None)
        self.add_item(Button(label="Rock",emoji="🪨",custom_id="rps_rock_"+choice.lower()))
        self.add_item(Button(label="Paper",emoji="📰",custom_id="rps_paper_"+choice.lower()))
        self.add_item(Button(label="Scissors",emoji="✂️",custom_id="rps_scissors_"+choice.lower()))

class NCView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in ABC: self.add_item(Button(label=i,custom_id="nc_column_"+i,row=0))
        for i in range(1,4): self.add_item(Button(label=str(i),custom_id="nc_row_"+str(i),row=1))

async def ChatGPT(user:Member,prompt:str=None,personality:str="balanced",edit=None,max_tokens:int=500,
                  chatOverride:[{"role":str,"content":str}]=None,model:GPT_Model=GPT_Model.GPT3) -> tuple[str,int]:
    if not user: return # // User is required for ID and credits
    if not prompt and not chatOverride: return # // A prompt or chat override is required otherwise - what are we doing?

    if not chatOverride:
        # // Make all substitutions. According to chatgpt random.shuffle() is less efficient than randint()
        sysMsg = PERSONALITIES[personality][0].replace("{DEFAULT}",DEFAULT_PERSONALITY).replace("{BOTNAME}",NAMES[randint(0,len(NAMES)-1)]).replace("{USERNAME}",user.nick)

    userId = user.id
    response = await to_thread(ChatCompletion.create,
        model=str(model),
        temperature=0.5,
        max_tokens=max_tokens,
        top_p=0.6,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True if edit else False,

        messages = chatOverride if chatOverride else 
        [{"role": "system","content": sysMsg},
        {"role": "user","content": prompt}]
    )

    if isinstance(response,str): return FailEmbed("Generation Failed.",response)

    file = File(encodeBotBin({"userid":userId,"personality":PERSONALITIES[personality][3]}),filename="data.png")
    
    # // If edit was provided, we can stream the response. With a delay of 1 second because of rate limits and to make it more readable especially on phones.
    if edit:
        lastChunk,msg = time_ns(),""
        for chunk in response:
            msg += chunk["choices"][0]["delta"].get("content","")
            if (lastChunk + 1_000_000_000) > time_ns(): # // 1 000 000 000 because nanoseconds - why is there no time_ms()?
                continue
            await edit(content="Generating...\n"+msg[:4096])
            lastChunk = time_ns()
        
        return msg[:4096],file,AskView()

    return response["choices"][0]["content"][:4096],file,AskView()

async def Transcribe(audio:bytes):
    # // According to https://platform.openai.com/docs/guides/speech-to-text/prompting, uhh ummm filler words will usually be omitted unless you prompt it
    audio = BytesIO(audio)
    audio.name = "voice-message.ogg"
    response = await OpenAIErrors(Audio.translate,model="whisper-1",file=audio,prompt="Uhh... ummm... I don't... give me a moment... let me think...",response_format="json")
    audio.close()
    if type(response) == str: return FailEmbed("Transcription Failed.",str(response))
    return response["text"]

async def Imagine(user:Member,prompt:str,amount:int,highRes:bool,variate:bool=False):
    response = None
    if variate:
        response = await OpenAIErrors(OpenAIImage.create_variation,image=prompt,
            n=amount,
            size=("1024x1024" if highRes else "256x256"),
            response_format = "b64_json"
        )
    else:
        response = await OpenAIErrors(OpenAIImage.create,prompt=prompt,
            n=amount,
            size=("1024x1024" if highRes else "256x256"),
            response_format = "b64_json",
        )
    
    if type(response) == str: return FailEmbed("Generation Failed.",str(response)),None,None
    response = response["data"]

    # // 1. We need to stitch the images together now
    # // ...and unstitch when a download is requested

    width,height,num,images = 0,0,len(response),[]
    for i in response:
        img = Image.open(BytesIO(b64decode(i["b64_json"])))
        images.append(img)
        width += img.width
        height = max(height,img.height)
    if num >= 4:
        width = ceil(width/2)
        height = width

    if num < 4: width += (STITCHBORDERPX*(num-1))
    else:
        width += STITCHBORDERPX
        height += STITCHBORDERPX
    
    borderX = Image.new("RGB",(STITCHBORDERPX,height,),(0,0,0,))
    stitched = Image.new("RGB",(width,height,),(0,0,0,))
    
    x = 0
    if num < 4:
        for i,v in enumerate(images,start=1):
            stitched.paste(v,(x,0))
            x += v.width
            if i != num:
                stitched.paste(borderX,(x,0,))
                x += STITCHBORDERPX
    else:
        borderY = Image.new("RGB",(width,STITCHBORDERPX,),(0,0,0,))
        y = 0
        for i,v in enumerate(images,start=1):
            stitched.paste(v,(x,y))
            x += v.width
            if i == 2:
                y += v.height
                stitched.paste(borderY,(0,y,))
                y += STITCHBORDERPX
                x = 0
            elif i != num: # // If we have moved to the next row we don't need to place X STITCHBORDERPX, hence elif
                stitched.paste(borderX,(x,y,))
                x += STITCHBORDERPX
        del borderY,y

    data = BytesIO()
    stitched.save(data,format="PNG")
    data.seek(0)
    file = File(data,filename="image.png")
    embed = SuccessEmbed(("Generation complete: "+prompt[:200]) if type(prompt) == str else "")
    embed.set_image(url="attachment://image.png")
    view = ImageView(amount)

    data.close()
    
    return embed,file,view