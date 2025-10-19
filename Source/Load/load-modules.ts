import type { BotClient } from "../bot-client.ts";
import { promises as fsPromises } from "fs";
import path from "path";
import { pathToFileURL } from "url";
import type { ModuleInterface } from "../Types/module-interface.ts";
import { Collection } from "discord.js";

export default async function LoadModules(client: BotClient) {
	client.modules = new Collection();

	const moduleFolderPath = path.join(import.meta.dirname, "..", "Modules");

	for await (const entry of fsPromises.glob("**/*.ts", { cwd: moduleFolderPath })) {
		const filePath = pathToFileURL(path.join(moduleFolderPath, entry)).href;
		const module = (await import(filePath)).default as ModuleInterface;
		if (module.load as unknown && module.unload as unknown) {
			client.modules.set(path.basename(entry, ".ts"), module);
			module.load(client);
		} else {
			throw new TypeError(`The command at ${filePath} is missing a required "data" or "execute" property.`);
		}
	}
}