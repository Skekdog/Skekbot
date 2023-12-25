from os import chdir
from pathlib import Path
from logging import getLogger
from typing import Literal, Tuple, TypeVar

from sqlite3 import connect, Error

chdir(Path(__file__).parent.parent)

logger = getLogger(__name__)
info, warn, error = logger.info, logger.warn, logger.error

db = connect("database.sqlite")
cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS userdata (
    id INTEGER PRIMARY KEY,
    openaicredituse INTEGER DEFAULT 0,
    openaibonuscredits INTEGER DEFAULT 0
)""") ## Credit use is stored as an integer representing the amount in pennies (or well, cents)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcementchannels ( id INTEGER PRIMARY KEY )
""")

db.commit()

T = TypeVar("T", bound=Tuple)
def get(table: Literal["userdata", "announcementchannels"], id: int, default: T, values: str = "*") -> T:  # type: ignore
    try:
        res = cursor.execute(f"SELECT {values} FROM {table} WHERE id = {id}").fetchall()
        return res[0] if len(res) > 0 else default
    except Error as err:
        error(err)
        return err # type: ignore

def update(table: Literal["userdata", "announcementchannels"], id: int, column: str, value: int | float) -> None | Error:
    res = get(table, id, (0,))
    if issubclass(res.__class__, Error): error(res); return res # type: ignore
    if not res:
        cursor.execute(f"INSERT INTO {table} (id) VALUES ({id})")
    cursor.execute(f"UPDATE {table} SET {column} = {value} WHERE id = {id}")
    db.commit()

def sql_execute(command: str):
    cursor.execute(command)
    db.commit()