"""
A set of utilities, designed for Skekbot.
"""

from PIL import Image
from typing import Any
from skekenums import *

import time,os,io

up = "userprivileges.txt"
ud = "userdata.txt"

dailyBudget = 0.04
prices = {
    Resolution.Low:0.016,
    Resolution.Med:0.018,
    Resolution.High:0.02,

    AI_API.Chat:0.002,
}

db = os.path.dirname(os.path.abspath(__file__))+"/../database"
os.chdir(db)
    
def evaluateRefresh(string:str) -> str or None:
    string = string.split("=")[1]
    vals = string.split(";")
    lastTime,interval = float(vals[0]),float(vals[1])
    curTime = time.time()
    if lastTime + interval > curTime:
        return
    return str(curTime - (curTime%interval))
    
def readFromKey(file:str,key:str,index:int|list[int]|None=None,default:Any=None) -> list[Any]:
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

    with open(file,"r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            kv = line.split("=")
            if len(kv)<2: continue
            vals = kv[1].split(";")
            if line.startswith("__lastrefresh"):
                newTime = evaluateRefresh(line)
                if not newTime: continue
                newLines=["__lastrefresh="+newTime+";"+vals[1]]
                f.truncate(0)
                f.writelines(newLines)
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

def getCost(model:AI_API,tokens=0,resolution="256x256",amount=1) -> float:
    "Calculates cost of using an OpenAI command."
    return prices[resolution]*amount if model == AI_API.Image or model == AI_API.Variation else prices[model]*tokens/1000

def spendCredits(userID:int,model:AI_API,tokens=0,resolution="256x256",amount=1) -> tuple[float,float]:
    "Deducts calculated credits from the user. Returns calculated value and remaining out of daily budget."

    userDailyBudget = dailyBudget+float(readFromKey(up,userID,0,default=0)[0])
    currentSpend = float(readFromKey(ud,userID,0,default=0)[0])
    cost = getCost(model,tokens,resolution,amount)

    writeToKey(ud,userID,{0:cost+currentSpend})
    remaining = userDailyBudget-cost-currentSpend
    return cost, remaining

def checkCredits(userID:int,model:AI_API,resolution=Resolution.Low,amount=1) -> bool|int:
    "Returns bool for images. Returns amount of tokens that can be used with a chat model, or False if none."
    
    userDailyBudget = dailyBudget+float(readFromKey(up,userID,0,default=0)[0])
    spends = float(readFromKey(ud,userID,0,default=0)[0])

    if model in [AI_API.Image,AI_API.Variation]:
        return ((userDailyBudget - spends >= (prices[resolution]*amount)),(userDailyBudget - spends))
    elif model in [AI_API.Chat]:
        return (((userDailyBudget - spends)*1000/prices[model]),(userDailyBudget - spends)) if ((userDailyBudget - spends)*1000/prices[model] > 0) else (False,(userDailyBudget - spends))
    

def toJpeg(file:bytes) -> io.BytesIO:
    "Converts an image file to JPEG."

    image = Image.open(io.BytesIO(file))
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    b = io.BytesIO()
    image.save(b,"JPEG")
    b.seek(0)
    return b

def toPng(file:bytes) -> io.BytesIO:
    "Converts an image file to PNG."

    image = Image.open(io.BytesIO(file))
    b = io.BytesIO()
    image.save(b,"PNG")
    b.seek(0)
    return b