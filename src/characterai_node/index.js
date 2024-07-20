const CharacterAI = require("node_characterai")
const Chat = require("node_characterai/chat")
const characterAI = new CharacterAI();

characterAI.requester.puppeteerPath = process.env.SKEKBOT_CHROMIUM_PATH;

// CLI Args:
// 0: Node.exe
// 1: Start directory

// 2: Access token
// 3: Character ID
// 4: History ID
// 5: Prompt

// Returns:
// 0: externalId (historyId)
// 1: srcCharacterName
// 2: srcAvatarFileName
// 3: text (response)

// TODO: this process should be running for as long as Skekbot runs, stdin used to send prompts to specified character of specified history

(async () => {
    const args = process.argv;

    const token = args[2];
    const characterId = args[3];
    var historyId = args[4];
    if (historyId === "None") {
        historyId = null;
    }
    const prompt = args[5];

    await characterAI.authenticateWithToken(token);

    var chat;
    if (historyId === null) {
        request = await characterAI.requester.request("https://beta.character.ai/chat/history/create/", {
            body: JSON.stringify({
                character_external_id: characterId,
                history_external_id: null,
            }),
            method: "POST",
            headers: characterAI.getHeaders()
        });
        if (request.status() === 200) {
            const json = JSON.parse(await request);
            chat = new Chat(characterAI, characterId, json);
        }
        else Error("Could not create a new chat.");
    } else {
        chat = await characterAI.createOrContinueChat(characterId, historyId);
    }
    const response = await chat.sendAndAwaitResponse(prompt, true);

    console.log(`SKEKBOT OUTPUT: ${response.chat.externalId}`);
    console.log(`SKEKBOT OUTPUT: ${response.srcCharacterName}`);
    console.log(`SKEKBOT OUTPUT: ${response.srcAvatarFileName}`);
    console.log(`SKEKBOT OUTPUT: ${response.text}`);
    characterAI.requester.uninitialize();
})();
