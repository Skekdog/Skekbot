"""
A set of utilities, designed for Skekbot.
"""

from PIL import Image
from typing import Any
from skekenums import *

import time,os,io
import mysql.connector as sql

up = "userprivileges"
ud = "userdata"
print("Connecting...")
db = sql.connect(
    host=os.environ.get("MYSQLHOST"),
    user=os.environ.get("MYSQLUSER"),
    password=os.environ.get("MYSQLPASSWORD"),
    database=os.environ.get("MYSQLDATABASE"),
    port=os.environ.get("MYSQLPORT"),
)
print("Connected to database!")
db.autocommit = True
dbCur = db.cursor()

dailyBudget = 2
prices = {
    Resolution.Low:0.016,
    Resolution.Med:0.018,
    Resolution.High:0.02,

    AI_API.Chat:0.002,
    AI_API.Completion:0.0005,
    ## If I ever decide to use GPT4
    ## AI_API.GPT4:0.03,
    ## AI_API.GPT4PLUS:0.06,
}

current_dir = os.path.dirname(os.path.abspath(__file__))


class SQLDict(dict):
    def __str__(self) -> str:
        len = self.__len__()
        fin = ""
        for i,v in enumerate(self.items()):
            fin += (str(v[0])+" = "+str(v[1])+("," if i < len-1 else ""))
        return fin
    
    def keys(self) -> str:
        len = self.__len__()
        fin = ""
        for i,v in enumerate(list(super().keys())):
            fin += str(v)+("," if i < len-1 else "")
        return fin

    def values(self) -> str:
        len = self.__len__()
        fin = ""
        for i,v in enumerate(list(super().values())):
            fin += str(v)+("," if i < len-1 else "")
        return fin

def readFromKey(database:str,key:str,columns:str="*",default=None) -> tuple[Any]:
    """
    Returns the values stored at the key in table. Returns None if key does not exist.
    A default can be set as the return value, instead of None.
    If file has a `__!!lastrefresh` key, this function will also refresh the file if the 2nd value in seconds has passed since the first value.
    """

    if type(columns) is not str:
        raise TypeError(f"Expected str for columns, got {type(columns)}")
    global dbCur
    default = (default,)
    key=str(key)
    key = "'"+key+"'"

    try:
        try:
            dbCur.execute(f"SELECT * FROM {database} WHERE id = 'lastrefresh'")
            values = dbCur.fetchone()
            last = values[1]
            period = values[2]
            curTime = time.time()
            newPeriod = curTime-(curTime%period)
            if curTime >= ((last+(period-(last%period))%period) + period):
                #// It's low noon
                dbCur.execute(f"TRUNCATE {database}")
                dbCur.execute(f"INSERT INTO {database} (id,credits,characters) VALUES ('lastrefresh',{newPeriod},{period})")
                return default
        except sql.errors.ProgrammingError:
            pass
        except TypeError:
            pass
        dbCur.execute(f"SELECT {columns} FROM {database} WHERE id = {key}")
        val = dbCur.fetchone()
        if val is None: return default
        return val if (len(val) > 0 and any(val)) else default
    except sql.errors.DatabaseError as err:
        print(err)
        print("Reconnecting...")
        db = sql.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=os.environ.get("MYSQLPORT"),
        )
        print("Reconnected to database!")
        db.autocommit = True
        dbCur = db.cursor()
        return readFromKey(database,key[1:-1],columns=columns,default=default[0])
    
def writeToKey(database:str,key:str,values:dict,encloseVals:str="") -> None:
    "Replaces the values at columns of key in database with values. If the key does not exist, it is added."
    if not isinstance(values,dict):
        raise TypeError(f"Expected dict for values, got {type(values)}")
    
    key=str(key)
    key = "'"+key+"'"
    if type(values) is not SQLDict:
        values = SQLDict(values)
    global dbCur

    try:
        dbCur.execute(f"SELECT * FROM {database} WHERE id = {key}")
        if dbCur.fetchone() is not None:
            dbCur.execute(f"UPDATE {database} SET {str(values)} WHERE id = {key}")
        else:
            dbCur.execute(f"INSERT INTO {database} (id,{values.keys()}) VALUES ({key},{encloseVals}{values.values()}{encloseVals})")
    except sql.errors.DatabaseError as err:
        print(err)
        print("Reconnecting...")
        db = sql.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=os.environ.get("MYSQLPORT"),
        )
        print("Reconnected to database!")
        db.autocommit = True
        dbCur = db.cursor()
        return writeToKey(database,key[1:-1],values,encloseVals=encloseVals)

    
def deleteKey(database:str,key:str) -> None:
    "Deletes a key from a database."
    key = str(key)
    global dbCur
    try:
        dbCur.execute(f"DELETE FROM {database} WHERE id = {key}")
    except sql.errors.DatabaseError as err:
        print(err)
        print("Reconnecting...")
        db = sql.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=os.environ.get("MYSQLPORT"),
        )
        print("Reconnected to database!")
        db.autocommit = True
        dbCur = db.cursor()
        deleteKey(database,key)

def spendCredits(userID:int,model:AI_API,tokens=0,resolution="256x256",amount=1) -> tuple[float,float]:
    "Calculate costs and deduct credits from the user. Returns calculated value and remaining out of daily budget."

    userDailyBudget = dailyBudget+float(readFromKey(up,userID,"credits",default=0)[0])
    currentSpend = float(readFromKey(ud,userID,"credits",default=0)[0])
    cost:float
    if model in [AI_API.Image,AI_API.Variation]:
        cost = prices[resolution]*amount
    elif model in [AI_API.Chat,AI_API.Completion]:
        cost = prices[model]*tokens/1000

    writeToKey(ud,userID,{"credits":cost+currentSpend})
    remaining = userDailyBudget-cost-currentSpend
    return cost, remaining

def checkCredits(userID:int,model:AI_API,resolution=Resolution.Low,amount=1) -> bool|int:
    "Returns bool for images. Returns amount of tokens that can be used with a chat model, or False if none."

    print(readFromKey(up,userID,"credits",default=0)[0])
    userDailyBudget = dailyBudget+float(readFromKey(up,userID,"credits",default=0)[0])
    spends = float(readFromKey(ud,userID,"credits",default=0)[0])

    if model in [AI_API.Image,AI_API.Variation]:
        return userDailyBudget - spends >= (prices[resolution]*amount)
    elif model in [AI_API.Chat,AI_API.Completion]:
        return (userDailyBudget - spends)*1000/prices[model] if (userDailyBudget - spends)*1000/prices[model] > 0 else False
    

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

if __name__ == "__main__":
    readFromKey("userdata",534828861586800676)