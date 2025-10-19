import { Events, Message } from "discord.js";
import type { ModuleInterface } from "../Types/module-interface.ts";
import sanitisePings from "../Utility/sanitise-pings.ts";

const IM = ["im", "i'm", "i’m"];
const MAX_LENGTH = 50;

async function onMessage(message: Message) {
	if (message.author === message.client.user) return;

	const content = message.cleanContent;
	const lowerContent = content.toLowerCase();

	let startIndex;

	const words = lowerContent.split(" ");
	for (const word of words) {
		if (word === "i") {
			if (words[words.indexOf(word) + 1] === "am") {
				startIndex = lowerContent.indexOf("am") + word.length + 1;
				break;
			}
		}

		if (IM.includes(word)) {
			startIndex = lowerContent.indexOf(word) + word.length + 1;
			break;
		}
	}

	if (!startIndex || startIndex >= content.length) return;

	let name: string | undefined = content.slice(startIndex);
	name = name.split(".")[0]?.split(",")[0]?.slice(0, MAX_LENGTH).trim();

	if (!name) return;

	name = sanitisePings(name);

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