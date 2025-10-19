import type { BotClient } from "./bot-client.ts";
import { promises as fsPromises } from "fs";
import path from "path";
import { pathToFileURL } from "url";
import type { ModuleInterface } from "./module-interface.ts";

export default async function LoadModules(client: BotClient) {
	const moduleFolderPath = path.join(import.meta.dirname, "Modules");

	for await (const entry of fsPromises.glob("**/*.ts", { cwd: moduleFolderPath })) {
		const filePath = pathToFileURL(path.join(moduleFolderPath, entry)).href;
		const command = (await import(filePath)).default as ModuleInterface;
		if (command.load as unknown && command.unload as unknown) {
			command.load(client);
		} else {
			throw new TypeError(`The command at ${filePath} is missing a required "data" or "execute" property.`);
		}
	}
}