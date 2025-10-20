import path from "path";
import { pathToFileURL } from "url";
import type { CommandInterface } from "../Types/command-interface.ts";
import type { BotClient } from "../bot-client.ts";

export default async function LoadCommand(client: BotClient, commandName: string) {
	const fileUrl = pathToFileURL(path.join(import.meta.dirname, "..", "Commands", commandName)).href + ".ts?t=" + Date.now();
	const newCommand = (await import(fileUrl)).default as CommandInterface;
	if (newCommand.data && newCommand.execute as unknown) {
		client.commands.set(commandName, newCommand);
	} else {
		throw new TypeError(`Command ${commandName} is missing a required "data" or "execute" property.`);
	}
}
