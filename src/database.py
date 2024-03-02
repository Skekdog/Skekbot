from os import chdir
from pathlib import Path
from logging import getLogger
from time import time
from typing import Literal, TypeVar, Tuple

from sqlite3 import connect, Error

chdir(Path(__file__).parent.parent)

logger = getLogger("skekbot")
info, warn, error = logger.info, logger.warn, logger.error

_db = connect("database.sqlite")
_cursor = _db.cursor()

CREDIT_REFRESH_FREQ = 86400

def _execute(statement: str):
    info(f"Executing statement: {statement}")
    return _cursor.execute(statement)

_execute("""
    CREATE TABLE IF NOT EXISTS userdata (
        id INTEGER PRIMARY KEY,
        openaicredituse INTEGER DEFAULT 0,
        openaibonuscredits INTEGER DEFAULT 0
    )
""") # Credit use is stored as an integer representing the amount in pennies (or well, cents)
_execute("""
    CREATE TABLE IF NOT EXISTS announcementchannels ( id INTEGER PRIMARY KEY )
""")
_execute("""
    CREATE TABLE IF NOT EXISTS botdata (
        id TEXT PRIMARY KEY,
        value TEXT
    )
""")
_db.commit()

def isCreditRefreshDue():
    global lastcreditrefresh
    assert isinstance(lastcreditrefresh, float) or isinstance(lastcreditrefresh, int)
    curTime = time()
    if curTime > (lastcreditrefresh + CREDIT_REFRESH_FREQ):
        lastcreditrefresh = (curTime - (curTime % CREDIT_REFRESH_FREQ)) + CREDIT_REFRESH_FREQ
        return True
    return

T = TypeVar("T", bound=Tuple[int | float | None, ...],)
def get(table: Literal["userdata", "announcementchannels", "botdata"], id: int | str, default: T, values: str = "*") -> T | Error:
    if isinstance(id, str) and id != "*":
        id = f"'{id}'"
    if table == "userdata":
        newRefresh = isCreditRefreshDue()
        if newRefresh:
            _execute("UPDATE userdata SET openaicredituse = 0")
            update("botdata", "lastcreditrefresh", "value", str(lastcreditrefresh))
    try:
        res = _execute(f"SELECT {values} FROM {table} WHERE id = {id}").fetchall()
        return res[0] if len(res) > 0 else default
    except Error as err:
        error(err)
        return err
    
if isinstance(lastcreditrefresh := get("botdata", "lastcreditrefresh", (0, ), "value"), Error):
    lastcreditrefresh = 0
else:
    lastcreditrefresh = float(lastcreditrefresh[0])

def update(table: Literal["userdata", "announcementchannels", "botdata"], id: int | str, column: str, value: int | float | str) -> Error | None:
    if isinstance(id, str):
        id = f"'{id}'"
    _execute(f"INSERT OR IGNORE INTO {table} (id, {column}) VALUES ({id}, {value})")
    _execute(f"UPDATE {table} SET {column} = {value} WHERE id = {id}")
    _db.commit()

def sql_execute(statement: str, get: bool = False):
    if get: return _execute(statement).fetchall()
    _execute(statement)
    _db.commit()