import { Events, Message } from "discord.js";
import type { ModuleInterface } from "../Types/module-interface.ts";
import { sanitiseMentions } from "$lib/mentions.ts";

const IM = ["im", "i'm", "i’m"];
const MAX_LENGTH = 75;

async function onMessage(message: Message) {
	if (message.author.bot) return;

	const content = message.cleanContent;
	const lowerContent = content.toLowerCase();

	let startIndex: number | undefined;
	let currentIndex = 0;

	const words = lowerContent.split(" ");
	for (let i = 0; i < words.length; i++) {
		const word = words[i];
		if (!word) break;

		currentIndex += word.length + 1;

		if (word === "i" && words[i + 1] === "am") {
			startIndex = currentIndex + 2;
		} else if (IM.includes(word)) {
			startIndex = currentIndex;
		}
	}

	if (!startIndex || startIndex >= content.length) return;

	let name: string | undefined = content.slice(startIndex);
	name = name.split(".")[0]?.split(",")[0]?.slice(0, MAX_LENGTH).trim();

	if (!name) return;

	name = sanitiseMentions(name);

	await message.reply({
		content: `Hi ${name}, I'm Skekbot!`,
		allowedMentions: {
			repliedUser: false,
		},
	});
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
