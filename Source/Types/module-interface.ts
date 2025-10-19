import type { BotClient } from "../bot-client.ts";

export interface ModuleInterface {
	load(client: BotClient): Promise<void>,
	unload(client: BotClient): Promise<void>,
}