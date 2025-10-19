import { Client, Collection } from "discord.js";
import type { CommandInterface } from "./Types/command-interface.ts";
import type { ModuleInterface } from "./Types/module-interface.ts";

export class BotClient extends Client {
	commands: Collection<string, CommandInterface> = new Collection();
	modules: Collection<string, ModuleInterface> = new Collection();
}

export function isBotClient(client: unknown): client is BotClient {
	return client instanceof BotClient;
}