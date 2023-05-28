
# Skekbot
A mostly-for-fun discord bot, written in Python using Discord.py.

## imagine
Uses OpenAI's DALL-E 2 model to generate images given a prompt.
Prompts must follow OpenAI's policies, as detailed here: https://openai.com/policies/usage-policies
Upon generating an image, you are able to generate variations of the image. These will be generated in 1024x1024 resolution.

To use this command (and the variations function), you must have enough credit. You can learn more about credits with the `/credits` command.

`Prompt:` Prompt to generate images from. This is a required field.
`Amount:` Amount of images to generate. This defaults to 1.
`Resolution:` Resolution of images to generate. Due to OpenAI, the actual resolution may be different. This defaults to 256x256.

Pricing per image for resolution:
> `1024x1024:` $0.020
> 
> `512x512:` $0.018
> 
> `256x256:` $0.016

## variations
 Generate variations of an image. You must attach the image to the command.
`Image:` The image to generate variations of.
`Amount:` Amount of variations to generate.

## credits
 Shows information about the credit system.

## help
 You know what this command does. You can specify a command field to get thorough information on a given command.

## lucky
Provides a random fortune cookie message.

## speech_synthesis
Uses ElevenLabs' AI to generate speech.
> `Prompt:` Prompt to synthesise speech from.
> 
> `Model:` Voice model to use.
> 
> `Multilingual:` Whether to use the multilingual model.

## translate
Uses DeepL to translate text. To use the 2nd language list, set a language in the first list, the 2nd list will override it.
> `Suffocating Letters:` Text to translate
> 
> `New Language:` Language to translate into
> 
> `New Language 2:` Due to a Discord limitation, each parameter can only have 25 options. Use this if the desired language is not in the first list.

## coin_flip
Flips an unbiased coin.

## ask
Commands for asking AI models.

Parameters for all commands:
> `Prompt:` Prompt to provide the AI.

Parameters for GPT and Babbage:
> `Temperature:` How non-deterministic the AI will be. A high temperature means the AI is more likely to generate different responses.
> 
> `Presence_Penalty:` Penalty to apply to the AI for not starting new topics.
> 
> `Frequency_Penalty:` Penalty to apply to the AI for repeating the same words.

***GPT:*** ask OpenAI's ChatGPT model (gpt-3.5-turbo)
Personality: Personality of the AI.

***Babbage:*** ask OpenAI's Completions model (text-babbage-002)

***CharacterAI:*** ask a Character on https://beta.character.ai/. Does not cost credits.
> `Character_ID:` ID of the character, can be found in the url: `https://beta.character.ai/.../chat?char=CHARACTER ID`

***CharacterAI Preset:*** ask a preset Character on https://beta.character.ai/. Does not cost credits.
> `Character`: The character to ask.


## converse
Commands for conversing with AI models. To continue a conversation, send a message in the attached thread when this command is executed.
Parameters for all commands:
> `Prompt:` Intial prompt to provide the AI.

***GPT:*** converse with OpenAI's ChatGPT model (gpt-3.5-turbo)
> `Personality:` Personality of the AI.

## poll
 Commands for interacting with polls.
***Create:*** create a poll
> `Question:` Question to poll on. A question mark is automatically added.
> 
> `Expiry:` Either "at time" or "upon reaching X reactions".
> 
> "at time" will end the poll at the unix timestamp provided in the expiry_value argument.
> "upon reaching X reactions" will end the poll once a total of X (as specified in the expiry_value argument) valid reactions have been reached.

> `Options:` A list of options to add to the poll. Each option should be separated by a semicolon (;) and there is a limit of 9 options.
