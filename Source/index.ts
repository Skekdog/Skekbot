import { Events, GatewayIntentBits } from "discord.js";
import { BotClient } from "./bot-client.ts";
import LoadCommands from "./load-commands.ts";
import LoadModules from "./load-modules.ts";

const TOKEN = process.env["BOT_ID"];

const client = new BotClient({
	intents: [
		GatewayIntentBits.Guilds,
		GatewayIntentBits.MessageContent,
		GatewayIntentBits.GuildMessages,
	],
});

client.once(Events.ClientReady, (readyClient) => {
	console.log(`Ready! Logged in as ${readyClient.user.tag}`);
	LoadModules(client);
	LoadCommands(client);
});

client.login(TOKEN);