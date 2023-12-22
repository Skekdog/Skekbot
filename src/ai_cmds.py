from time import time_ns
from typing import Any, Literal
from openai import AsyncOpenAI
from tiktoken import encoding_for_model
from database import get, update
from os import environ

from asyncio import create_task

openAiClient = AsyncOpenAI(api_key="")


OPENAI_BUDGET = 0.025
MAX_TOKENS = 850 # This was determined by spamming nonsense into tokeniser to get ~4000 characters.

PRICING_CHATINPUT = (0.001 / 1000) # $0.001 per 1k input tokens
PRICING_CHATOUTPUT = (0.0015 / 1000) # $0.0015 per 1k output tokens
PRICING_IMAGE = (0.016) # $0.016 for a 256x256 image.
PRICING_AUDIO = (0.006 / 60) # $0.006 per minute

def hasEnoughCredits(id: int, intentType: Literal["chat", "image", "audio"], intentAmount: int) -> bool:
    usage, bonus = get("userdata", id, "(openaicredituse, openaibonuscredits)")

    approxCost = float("inf")
    if intentType == "chat":
        approxCost = (intentAmount * PRICING_CHATINPUT) + ((MAX_TOKENS - intentAmount) * PRICING_CHATOUTPUT)
    elif intentType == "audio": approxCost = (intentAmount * PRICING_AUDIO)
    elif intentType == "image": approxCost = (intentAmount * PRICING_IMAGE)

    return (((OPENAI_BUDGET + bonus) - usage) - approxCost) > 0 # type: ignore

def chargeUser(id: int, intentType: Literal["chat", "image", "audio"], intentAmount: int, intentAmount2: int | None):
    charge = 0
    if intentType == "chat" and intentAmount2:
        charge = (intentAmount * PRICING_CHATINPUT) + (intentAmount2 * PRICING_CHATOUTPUT)
    elif intentType == "image": charge = intentAmount * PRICING_IMAGE
    elif intentType == "audio": charge = intentAmount * PRICING_AUDIO
    update("userdata", id, "openaicredituse", get("userdata", id, "openaicredituse", (0,) )[0] + charge)

async def chatGPT(id: int, prompt: str, update: Any):
    completion = create_task(openAiClient.chat.completions.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=[
            {"role": "system", "content": "Respond objectively and exactly how the user asks"},
            {"role": "user", "content": prompt}
        ]
    ))
    
    inputTokens = len(encoding_for_model("gpt-3.5-turbo").encode(prompt))
    outputTokens, msg, lastTime = 0, "", time_ns()
    async for chunk in await (completion):
        choice = chunk.choices[0]
        if choice.delta.content:
            outputTokens += 1
            msg += (choice.delta.content or "")
            if (lastTime + 1_000_000_000) > time_ns(): continue
            print("doing")
            lastTime = time_ns()
            await update(content=msg)
        if choice.finish_reason:
            await update(content=msg+(choice.delta.content or ""))
            return chargeUser(id, "chat", inputTokens, outputTokens)
        