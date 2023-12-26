import os
from asyncio import create_task
from random import randint
from typing import Callable, List, Literal, Coroutine, Tuple

from io import BytesIO
from pydub import AudioSegment
from openai import AsyncOpenAI
from tiktoken import encoding_for_model
from time import time_ns
from PIL import Image

from database import get, update

openAiClient = AsyncOpenAI(api_key=os.environ["SKEKBOT_OPENAI_TOKEN"])

OPENAI_BUDGET = 0.02
MAX_TOKENS = 850 # This was determined by spamming nonsense into tokeniser to get ~4000 characters.

PRICING_CHATINPUT = (0.001 / 1000) # $0.001 per 1k input tokens
PRICING_CHATOUTPUT = (0.0015 / 1000) # $0.0015 per 1k output tokens
PRICING_IMAGE = (0.016) # $0.016 for a 256x256 image.
PRICING_AUDIO = (0.006 / 60) # $0.006 per minute

def hasEnoughCredits(id: int, intentType: Literal["chat", "image", "audio"], intentAmount: int) -> bool:
    usage, bonus = get("userdata", id, (0, 0, ), "openaicredituse, openaibonuscredits")

    approxCost = float("inf")
    if intentType == "chat":
        approxCost = (intentAmount * PRICING_CHATINPUT) + ((MAX_TOKENS - intentAmount) * PRICING_CHATOUTPUT)
    elif intentType == "audio": approxCost = (intentAmount * PRICING_AUDIO)
    elif intentType == "image": approxCost = (intentAmount * PRICING_IMAGE)

    return (((OPENAI_BUDGET + bonus) - usage) - approxCost) > 0 # type: ignore

def chargeUser(id: int, intentType: Literal["chat", "image", "audio"], intentAmount: int, intentAmount2: int | None = None):
    charge = 0
    if intentType == "chat" and intentAmount2:
        charge = (intentAmount * PRICING_CHATINPUT) + (intentAmount2 * PRICING_CHATOUTPUT)
    elif intentType == "image": charge = intentAmount * PRICING_IMAGE
    elif intentType == "audio": charge = intentAmount * PRICING_AUDIO
    update("userdata", id, "openaicredituse", get("userdata", id, (0,), "openaicredituse")[0] + charge)
    return charge

def encodeImage(data: Tuple[str, ...]) -> BytesIO:
    # Stores binary data as a 512x? PNG.
    # Each Y stores 64 bytes.

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

def decodeImage(data: BytesIO) -> List[str]:
    img = Image.open(data, formats=["png"])

    width, height = img.size
    decodedList = []
    
    for y in range(height):
        section, thisByte = "", ""
        for x in range(width):
            if ((x % 8) == 0) and (x != 0):
                section += chr(int(thisByte, 2))
                thisByte = ""
            thisByte += str(img.getpixel((x, y)) // 255)
        decodedList.append((section + chr(int(thisByte, 2))).strip(chr(0)))

    return decodedList

UpdateCoroutine = Callable[[str, int], Coroutine[None, Tuple[str, bool], None]]
async def chatGPT(id: int, prompt: str, update: UpdateCoroutine):
    inputTokens = len(encoding_for_model("gpt-3.5-turbo").encode(prompt))
    if not hasEnoughCredits(id, "chat", inputTokens): return await update("You do not have enough credits to run this command.", True)

    completion = create_task(openAiClient.chat.completions.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=[
            {"role": "system", "content": "Respond objectively and exactly how the user asks"},
            {"role": "user", "content": prompt}
        ]
    ))
    
    outputTokens, msg, lastTime = 0, "", time_ns() - 1_000_000_000
    async for chunk in await (completion):
        choice = chunk.choices[0]
        if choice.delta.content:
            outputTokens += 1
            msg += (choice.delta.content or "")
            if (lastTime + 1_000_000_000) > time_ns(): continue
            lastTime = time_ns()
            await update(msg, False)
        if choice.finish_reason:
            await update(msg+(choice.delta.content or ""), False)
            return chargeUser(id, "chat", inputTokens, outputTokens)
        
async def imagine(id: int, prompt: str, update: UpdateCoroutine):
    pass

async def transcribe(id: int, audio: BytesIO) -> str | None: # streaming is not available for transcriptions
    audio.name = "audio.ogg"

    duration = round(len(AudioSegment.from_file(audio)) / 1000)
    if not hasEnoughCredits(id, "audio", duration): return

    chargeUser(id, "audio", duration)

    audio.seek(0)
    transcription = await openAiClient.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        prompt="Uh... um... pffpfp...",
        response_format="text"
    )
    audio.close()

    return transcription # type: ignore