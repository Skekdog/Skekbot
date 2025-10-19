import { Client, Collection } from "discord.js";
import type { CommandInterface } from "./command-interface.ts";

export class BotClient extends Client {
	commands: Collection<string, CommandInterface> = new Collection();
}

export function isBotClient(client: unknown): client is BotClient {
	return client instanceof BotClient;
}