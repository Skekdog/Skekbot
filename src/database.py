from os import chdir
from pathlib import Path
from logging import getLogger
from typing import Literal, TypeVar, Tuple

from sqlite3 import connect, Error

chdir(Path(__file__).parent.parent)

logger = getLogger("skekbot")
info, warn, error = logger.info, logger.warn, logger.error

_db = connect("database.sqlite")
_cursor = _db.cursor()

def _execute(statement: str):
    info(f"Executing statement: {statement}")
    return _cursor.execute(statement)

_execute("""CREATE TABLE IF NOT EXISTS userdata (
    id INTEGER PRIMARY KEY,
    openaicredituse INTEGER DEFAULT 0,
    openaibonuscredits INTEGER DEFAULT 0
)""") # Credit use is stored as an integer representing the amount in pennies (or well, cents)
_execute("""
    CREATE TABLE IF NOT EXISTS announcementchannels ( id INTEGER PRIMARY KEY )
""")
_db.commit()

Error = Error

T = TypeVar("T", bound=Tuple[int | float, ...])
def get(table: Literal["userdata", "announcementchannels"], id: int, default: T, values: str = "*") -> T | Error:
    try:
        res = _execute(f"SELECT {values} FROM {table} WHERE id = {id}").fetchall()
        return res[0] if len(res) > 0 else default
    except Error as err:
        error(err)
        return err

def update(table: Literal["userdata", "announcementchannels"], id: int, column: str, value: int | float) -> None | Error:
    res = get(table, id, (0,))
    if isinstance(res, Error):
        error(res)
        return res
    if not res:
        _execute(f"INSERT INTO {table} (id) VALUES ({id})")
    _execute(f"UPDATE {table} SET {column} = {value} WHERE id = {id}")
    _db.commit()

def sql_execute(statement: str, get: bool = False):
    if get: return _execute(statement).fetchall()
    _execute(statement)
    _db.commit()