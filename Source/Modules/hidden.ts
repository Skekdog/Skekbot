import { Events, Message } from "discord.js";
import type { ModuleInterface } from "../Types/module-interface";
import winkNLP, { type ItemToken, type ItsFunction } from "wink-nlp";
import model from "wink-eng-lite-web-model";
import { removeMentions } from "$lib/mentions";

const HIDDEN_USER_ID = "475851244737396740";

const ALLOWED_ABBREVIATIONS: Record<string, string> = {
	perms: "permissions",
	msgs: "messages",
	imgs: "images",
};

const nlp = winkNLP(model);
const { its } = nlp;

function extractNounsWithCorrectVerb(text: string): string | null {
	const doc = nlp.readDoc(text);

	const phrases: { text: string; plural: boolean }[] = [];

	let currentWords: string[] = [];
	let plural = false;

	doc.tokens().each((token: ItemToken) => {
		const pos = token.out(its.pos);
		const word = token.out(its.value);
		const lemma = token.out(its.lemma as ItsFunction<string>);

		const isPhrasePart = pos === "NOUN" || pos === "PROPN" || pos === "ADJ";

		if (isPhrasePart) {
			currentWords.push(word);

			if (pos === "NOUN") {
				plural = word !== lemma;
			}
			return;
		}

		flush();
	});

	flush();

	if (phrases.length === 0) return null;

	const nouns = phrases
		.map(({ text }) => {
			const cleaned = text.replace(/\b(a|an|the)\b/gi, "").trim();
			if (!cleaned) return null;

			let head = cleaned.split(/\s+/).pop() ?? cleaned;

			head = ALLOWED_ABBREVIATIONS[head.toLowerCase()] ?? head;

			return cleaned.replace(/\S+$/, head);
		})
		.filter(Boolean) as string[];

	if (nouns.length === 0) return null;

	const lastPhrase = phrases[phrases.length - 1];
	const isPlural = nouns.length > 1 || lastPhrase?.plural;

	let nounText: string;

	if (nouns.length === 1) {
		nounText = nouns[0]!;
	} else if (nouns.length === 2) {
		nounText = `${nouns[0]} and ${nouns[1]}`;
	} else {
		nounText =
			nouns.slice(0, -1).join(", ") + ", and " + nouns[nouns.length - 1];
	}

	return `${nounText} ${isPlural ? "are" : "is"}`;

	function flush() {
		if (!currentWords.length) return;

		phrases.push({
			text: currentWords.join(" "),
			plural,
		});

		currentWords = [];
		plural = false;
	}
}

async function onMessage(message: Message) {
	if (message.author.bot) return;

	if (message.author.id !== HIDDEN_USER_ID) return;
	if (Math.random() > 0.25) return;

	const content = message.cleanContent;

	if (!content || content.length < 3) return;

	const sanitisedContent = removeMentions(content);

	const noun = extractNounsWithCorrectVerb(sanitisedContent);

	if (!noun) return;

	// NOTE: DO NOT FOR THE LOVE OF LINUS TORVALDS ADD IS/ARE BEFORE HIDDEN I SERIOUSLY BEG OF YOU
	// I HAVE SHOT MYSELF IN THE FOOT WITH THIS GOD FORSAKEN FUNCTION TOO MANY TIMES
	// SERIOUSLY
	// amount of times i banged my head in the wall: 34
	await message.reply({
		content: `maybe the ${noun} hidden`,
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
