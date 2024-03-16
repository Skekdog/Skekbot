# Skekbot

[License](https://github.com/Skekdog/Skekbot/blob/master/LICENSE)

A Discord bot, written in Python using Discord.py.
Use /help for a list of commands.

To use, the following environment variables should be set:
- SKEKBOT_MAIN_TOKEN (for the bot itself)
- SKEKBOT_OPENAI_TOKEN (for Transcription)
- SKEKBOT_CHARACTERAI_TOKEN (for CharacterAI) - This can be obtained from browser DevTools > Storage > Local Storage > beta.character.ai > char_token > value
- SKEKBOT_ANNOUNCEMENT_WEBSOCKET (for announcements. Should be a WebSocket URI, such as `ws://example.com`)
- FFMpeg must also be available in PATH
- SKEKBOT_CHROMIUM_PATH [OPTIONAL] (for CharacterAI, if default does not work)

Additional configuration options are available in config.yaml.

### Setup
- Set all environment variables listed above (a restart will usually be required)
- Install requirements.txt
- Navigate to src/characterai_node
- Run `npm i` (NPM must be installed and set up!)
- Start the bot by running main.py!

### Privacy
- Usage of [OpenAI](https://openai.com/) and [DeepL](https://deepl.com) commands (translation and transcription) is temporarily recorded to keep track of expenses incurred and usage limits, associated by Discord user ID
- Messages sent in CharacterAI threads are sent to [Character.AI](https://beta.character.ai/) with the user's username attached
- Audio files used in transcription are sent to [OpenAI](https://openai.com/) anonymously
- Messages used in translation are sent to [DeepL](https://deepl.com) anonymously

### Credits
Skekbot uses [node_characterai](https://github.com/realcoloride/node_characterai) for CharacterAI interaction, licensed under MIT.