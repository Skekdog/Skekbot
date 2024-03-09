from typing import Any, Literal

from cachetools import cached
from io import BytesIO
from PIL import Image

from database import get, update, delete, Error # pyright: ignore[reportUnusedImport]

OPENAI_BUDGET = 0.005
PRICING_AUDIO = (0.006 / 60) # $0.006 per minute

def getAvailableCredits(id: int) -> float:
    result = get("userdata", id, (0, 0), "openaicredituse, openaibonuscredits")
    if isinstance(result, Error): return 0

    available = (OPENAI_BUDGET + result[1]) - result[0]
    return available

def getMaxCredits(id: int) -> float:
    result = get("userdata", id, (0,), "openaibonuscredits")
    if isinstance(result, Error): return 0

    return OPENAI_BUDGET + result[0]

def hasEnoughCredits(id: int, intentType: Literal["audio"], intentInput: int) -> tuple[bool, float, float]:
    "Returns a tuple of True if enough credits to do the specified operation, the amount of credits that have already been used, and the available credits."
    result = get("userdata", id, (0, 0), "openaicredituse, openaibonuscredits")
    if isinstance(result, Error): return False, 0, 0
    usage, bonus = result

    if intentType == "audio": approxCost = (intentInput * PRICING_AUDIO)

    available = ((OPENAI_BUDGET + bonus) - usage)
    return (available - approxCost) > 0, usage, available

def chargeUser(id: int, intentType: Literal["audio"], intentInput: int, currentSpend: float | None = None) -> float:
    charge = 0
    if intentType == "audio": charge = intentInput * PRICING_AUDIO

    if not currentSpend:
        _currentSpend = get("userdata", id, (0,), "openaicredituse")
        if isinstance(_currentSpend, Error): return 0
        currentSpend = _currentSpend[0]
    
    update("userdata", id, "openaicredituse", currentSpend + charge)
    return charge

@cached(cache={}) # pyright: ignore[reportUnknownArgumentType]
def encodeImage(data: tuple[str, ...]) -> BytesIO:
    # Stores binary data as a 512x? PNG.
    # Each Y stores 64 bytes.
    # Discord doesn't display small images in embeds, so this is hidden from the user. Cool!

    img = Image.new("1", (512, len(data)), 0)
    for y, i in enumerate(data):
        byteData = ""
        for byte in i.encode("ISO-8859-1"):
            byteData += bin(byte)[2:].zfill(8)
        for x, val in enumerate(byteData):
            img.putpixel((x, y), int(val))
    
    imgData = BytesIO()
    img.save(imgData, "png")
    imgData.seek(0)
    return imgData

@cached(cache={}) # pyright: ignore[reportUnknownArgumentType]
def decodeImage(data: BytesIO) -> list[str]:
    img = Image.open(data, formats=["png"])

    width, height = img.size
    decodedList: list[str] = []
    
    for y in range(height):
        section, thisByte = "", ""
        for x in range(width):
            if ((x % 8) == 0) and (x != 0):
                section += chr(int(thisByte, 2))
                thisByte = ""
            thisByte += str(img.getpixel((x, y)) // 255) # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        decodedList.append((section + chr(int(thisByte, 2))).strip(chr(0)))

    return decodedList

def spoiler_pad(source: str, maxLength: int) -> str:
    return f"||`{source+(" " * (len(source) - maxLength))}`||"

def first_intersection_index(list1: list[Any], list2: list[Any]) -> tuple[int, Any] | None:
    "Returns the index of the first intersection between two lists, and the element that was found."
    for idx, elem in enumerate(list1):
        if elem in list2:
            return (idx, elem)
    return None