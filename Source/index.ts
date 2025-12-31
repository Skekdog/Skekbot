import { Events } from "discord.js";
import LoadCommands from "./Load/load-commands.ts";
import LoadModules from "./Load/load-modules.ts";
import "./Web/server.ts";
import client from "./client.ts";
import { env } from "./Utility/env.ts";

const TOKEN = env.BOT_TOKEN;

client.once(Events.ClientReady, (readyClient) => {
	console.log(`Logged in as ${readyClient.user.tag}`);
	LoadModules(client);
	LoadCommands(client);
});

client.login(TOKEN);
