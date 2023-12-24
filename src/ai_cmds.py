import os
from asyncio import create_task
from typing import Callable, Literal, Coroutine, Tuple

from io import BytesIO
from pydub import AudioSegment
from openai import AsyncOpenAI
from tiktoken import encoding_for_model
from time import time_ns

from database import get, update

openAiClient = AsyncOpenAI(api_key=os.environ["SKEKBOT_OPENAI_TOKEN"])

OPENAI_BUDGET = 0.001
MAX_TOKENS = 850 # This was determined by spamming nonsense into tokeniser to get ~4000 characters.

PRICING_CHATINPUT = (0.001 / 1000) # $0.001 per 1k input tokens
PRICING_CHATOUTPUT = (0.0015 / 1000) # $0.0015 per 1k output tokens
PRICING_IMAGE = (0.016) # $0.016 for a 256x256 image.
PRICING_AUDIO = (0.006 / 60) # $0.006 per minute

def hasEnoughCredits(id: int, intentType: Literal["chat", "image", "audio"], intentAmount: int) -> bool:
    usage, bonus = get("userdata", id, "openaicredituse, openaibonuscredits", (0, 0, ))

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
    update("userdata", id, "openaicredituse", get("userdata", id, "openaicredituse", (0,) )[0] + charge)
    return charge

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

async def transcribe(id: int, audio: bytes) -> str | None: # streaming is not available for transcriptions
    data = BytesIO(audio)
    data.name = "audio.ogg"

    duration = round(len(AudioSegment.from_file(data)) / 1000)
    if not hasEnoughCredits(id, "audio", duration): return

    print(chargeUser(id, "audio", duration))

    data.seek(0)
    transcription = await openAiClient.audio.transcriptions.create(
        model="whisper-1",
        file=data,
        prompt="Uh... um... pffpfp...",
        response_format="text"
    )
    data.close()

    return transcription # type: ignore