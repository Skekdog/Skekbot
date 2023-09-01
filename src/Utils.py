"""
A set of utilities, designed for Skekbot.
"""

import datetime,time,os,io

from math import ceil
from itertools import zip_longest
from PIL import Image
from io import BytesIO
from requests import get

from discord import Embed,Colour

from Constants import *

db = os.path.dirname(os.path.abspath(__file__))+"/../database"
os.chdir(db)

def calculateCost(model,counts) -> float:
    if type(model).__name__ == "GPT_Model":
        return (PRICES[model][0]*counts["prompt_tokens"]/1000)+(PRICES[model][1]*counts["completion_tokens"]/1000)
    return PRICES[model]*counts

def getStringAfterWord(string:str,wordTargets:list[str],phraseTargets:list[str],ignore:list[str]):

    longestPhrase = 0
    for i in phraseTargets:
        if len(i) > longestPhrase: longestPhrase = len(i.split(" "))

    words = string.lower().split(" ")
    prevWords,word=[],""
    for i,v in enumerate(words):
        prevPhrase = ""
        for w in prevWords: prevPhrase += w + " "
        prevPhrase = prevPhrase[:-1]
        if (prevPhrase in phraseTargets) or (v in wordTargets):
            try:
                # // Loop until we find a word that isn't in ignore list. If we don't find any we use the final word
                index = 0-(len(prevPhrase.split(" "))-1 if v not in wordTargets else 0)
                while (word in ignore) or index <= 0: # // index <= 0 because we need the loop to start
                    index += 1
                    word = words[i+index]
            except IndexError: pass
        
        prevWords.append(v)
        if len(prevWords) > longestPhrase: prevWords.pop(0)
    return word
 
def evaluateRefresh(string:str) -> str or None:
    vals = string.split("=")[1].split(";")
    lastTime, interval, curTime = int(vals[0]), int(vals[1]), int(time.time())
    
    if lastTime + interval > curTime:
        return
    
    return str(int(curTime - (curTime%interval)))

def wipeFile(file:str,new:str) -> None:
    """
    Removes all keys from file and places `new`.
    """
    os.chdir(db)
    with open(file,"w") as f:
        f.write(new)
    
def readFromKey(file:str,key:str,index:int|list[int]|None=None,default=None) -> list[str]:
    """
    Returns the value stored at index in file. Returns default or None if key does not exist.
    If file has a `__lastrefresh` key, this function will also refresh the file if the 2nd value in seconds has passed since the first value.
    
    File: the name of the file.
    Index: the position where the value is, 0-indexed. Can be a list of values to retrieve.  Will return a list ordered from smallest index to largest index.
    """

    os.chdir(db)
    key = str(key)
    if type(index) is int:
        index = [index]
    if type(default) is not list:
        default = [default]

    with open(file,"r") as f:
        lines = f.readlines()
        for line in lines:
            kv = line.split("=")
            if len(kv)<2: continue
            vals = kv[1].split(";")
            if line.startswith("__lastrefresh"):
                newTime = evaluateRefresh(line)
                if not newTime: continue
                wipeFile(file,"__lastrefresh="+newTime+";"+vals[1])
                f.close()
                return default
            if line.startswith(key):
                if not index:
                    return [v.strip() for v in vals]
                return [z.strip() if z != "" else default[0] for k,z in enumerate(vals) if k in index]
        f.close()
    return default

def writeToKey(file:str,key:str,indexVals:dict[int,str]) -> None:
    """
    Replaces index with value in file.

    File: the name of the file.
    Key: the key.
    IndexVals: the values to set at index. If index is far off, will be padded with semi-colons.
    """

    os.chdir(db)
    key = str(key)

    with open(file,"r+") as f:
        lines = f.readlines()
        f.seek(0)
        newLines = lines

        lineNum = None
        maxIndex = 0
        for i,line in enumerate(lines):
            if not line.startswith(key): continue
            vals = line.split("=")[1].split(";")
            originalVals = {}
            for k,v in enumerate(vals):
                if v != "":
                    originalVals[k] = v
            for k,v in indexVals.items():
                originalVals[k] = str(v)
            indexVals = originalVals
            maxIndex = len(vals)-1
            lineNum = i
            break

        highestIndex = 0
        for k in indexVals:
            if k > highestIndex: highestIndex = k
        if highestIndex > maxIndex: maxIndex = highestIndex

        holdStr = ";"*maxIndex
        newStr = ""
        splt = holdStr.split(";")
        for k,_ in enumerate(splt):
            try: newStr += str(indexVals[k])
            except KeyError: pass
            newStr += ";" if k < len(splt)-1 else ""
        
        if lineNum is not None: newLines[lineNum] = (key+"="+newStr).strip()+"\n"
        else:
            try: newLines[-1] = newLines[-1]+"\n"
            except IndexError: pass
            newLines.append(key+"="+newStr)

        f.writelines(newLines)
        f.truncate()
        f.close()

    
def deleteKey(file:str,key:str) -> None:
    "Deletes a key from a file."

    os.chdir(db)
    key = str(key)

    with open(file,"r+") as f:
        lines = f.readlines()
        f.seek(0)
        newLines = lines
        for i,line in enumerate(lines):
            if line.startswith(key):
                newLines.pop(i)
                break

        f.writelines(newLines)
        f.truncate()
        f.close()

def checkCredits(userID,model,amount):
    availableCreds = readFromKey(D_UD,)+D_UP.get()
    cost = calculateCost(model,amount)


# def spendCredits(userID:int,model:AI_API,tokens=0,resolution="256x256",amount=1) -> tuple[float,float]:
#     "Deducts calculated credits from the user. Returns calculated value and remaining out of daily budget."

#     userDailyBudget = dailyBudget+float(readFromKey(D_UP,userID,0,default=0)[0])
#     currentSpend = float(readFromKey(D_UD,userID,0,default=0)[0])
#     cost = getCost(model,tokens,resolution,amount)

#     writeToKey(D_UD,userID,{0:cost+currentSpend})
#     remaining = userDailyBudget-cost-currentSpend
#     return cost, remaining

# def checkCredits(userID:int,model:AI_API,resolution=Resolution.Low,amount=1) -> bool|int:
#     "Returns bool for images. Returns amount of tokens that can be used with a chat model, or False if none."
    
#     userDailyBudget = dailyBudget+float(readFromKey(D_UP,userID,0,default=0)[0])
#     spends = float(readFromKey(D_UD,userID,0,default=0)[0])

#     if model in [AI_API.Image,AI_API.Variation]:
#         return ((userDailyBudget - spends >= (prices[resolution]*amount)),(userDailyBudget - spends))
#     elif model in [AI_API.Chat]:
#         return (((userDailyBudget - spends)*1000/prices[model]),(userDailyBudget - spends)) if ((userDailyBudget - spends)*1000/prices[model] > 0) else (False,(userDailyBudget - spends))

# // When each key ends
dataTypes = {
    "userid": 63,
    "personality": 71,
}

def evalPix(pix):
    if pix == 255: return "1"
    if pix == 0: return "0"
    return ""

def encodeBotBin(data:dict) -> BytesIO:
    y = 0
    for i,v in dataTypes.items(): y = max(ceil(v/8),y)
    size = (8,y)

    bin_dat = Image.new("L",size)

    lastBit = 0
    for k,v in data.items():
        for i,bit in zip_longest(range(lastBit,dataTypes[k]+1),bin(v)[2:],fillvalue=2): # // [2:] because bin starts with "0b"
            bin_dat.putpixel((i%8,i//8),(2 if bit == 2 else int(bit)*255)) # // 2 = NO DATA; 255 = ON; 0 = OFF ---- I'll call it trinary
        lastBit = dataTypes[k]+1
    
    b = BytesIO()
    bin_dat.save(b,format="PNG")
    bin_dat.close()
    b.seek(0)
    
    return b

def decodeBotBin(data:bytes) -> dict:
    img = Image.open(BytesIO(data))
    bin_dat = img.convert("L")
    pixels = bin_dat.getdata()
    img.close()
    bin_dat.close()
    
    pixels,decode = list(pixels),{i:"0b" for i in dataTypes}
    for i,v in enumerate(pixels):
        lowest = [256,""]
        for j,k in dataTypes.items():
            if i <= k and k < lowest[0]: lowest = [k,j]
        decode[lowest[1]]+=evalPix(v)
    for i,v in decode.items(): decode[i] = int(v,2)
    return decode

async def fetch(url,err_msg,send):
    try: res = get(url)
    except BaseException as e:
        print("Fetch from",url,"failed with exception",e)
        embed = FailEmbed(err_msg[0],err_msg[1])
        await send(embed=embed,ephemeral=True)
        return
    if res.status_code != 200:
        print("Fetch from",url,"failed with status",res.status_code)
        embed = FailEmbed(err_msg[0],err_msg[1])
        await send(embed=embed,ephemeral=True)
        return
    return res.content

def getPersonalityById(id:int,name:bool=False):
    for i,v in PERSONALITIES.items():
        if v[3] == id: return i if name else v[0]
    return ""

def toPNG(file:bytes) -> BytesIO:
    "Converts an image file to PNG."

    image = Image.open(BytesIO(file))
    b = BytesIO()
    image.save(b,"PNG")
    image.close()
    b.seek(0)
    return b