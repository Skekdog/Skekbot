import { Events, Message } from "discord.js";
import type { ModuleInterface } from "../module-interface.ts";

async function onMessage(message: Message) {
	if (message.content.toLowerCase() === "hi") await message.reply(":wave:");
}

const module: ModuleInterface = {
	async load(client) {
		client.on(Events.MessageCreate, onMessage);
	},
	async unload(client) {
		client.off(Events.MessageCreate, onMessage);
	},
};

export default module;