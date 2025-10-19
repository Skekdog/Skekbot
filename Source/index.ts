import { Events, GatewayIntentBits } from "discord.js";
import { BotClient } from "./bot-client.ts";
import LoadCommands from "./load-commands.ts";

const TOKEN = process.env["BOT_ID"];

const client = new BotClient({
	intents: [
		GatewayIntentBits.Guilds
	],
});

client.once(Events.ClientReady, (readyClient) => {
	console.log(`Ready! Logged in as ${readyClient.user.tag}`);
	LoadCommands(client);
});

client.login(TOKEN);