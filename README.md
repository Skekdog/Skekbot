# Skekbot

[License](https://github.com/Skekdog/Skekbot/blob/master/LICENSE)

A Discord bot, written in Python using Discord.py.
Use /help for a list of commands.

To use, the following environment variables should be set:
- SKEKBOT_MAIN_TOKEN (for the bot itself)
- SKEKBOT_OPENAI_TOKEN (for Transcription)
- SKEKBOT_CHARACTERAI_TOKEN (for CharacterAI) - This can be obtained from browser DevTools > Storage > Local Storage > beta.character.ai > char_token > value
- SKEKBOT_ANNOUNCEMENT_WEBSOCKET (for announcements. Should be a WebSocket URI, such as ws://example.com)

Additional configuration options are available in config.yaml.

### Why not more AI tools?
- Skekbot previously had commands for ChatGPT and DALL-E generation. These have since been removed; ChatGPT is available for free and DALL-E was (in the model used) rather costly for pretty lackluster results.
- CharacterAI provides AI that is fun and friendly, not trying to be informative or accurate, thus it feels reasonable to include.
- I also see some issue with image generation not being used in a gimmicky-fun sort of way, and as I just said they were not good in a gimmicky-fun way either.
- Transcription, on the other hand, is an actually useful feature to be integrated into Discord (given the newly-arrived voice messages), and it has good results with good prices.