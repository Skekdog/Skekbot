import path from "path";
import { pathToFileURL } from "url";
import type { ModuleInterface } from "../Types/module-interface.ts";
import type { BotClient } from "../bot-client.ts";

export default async function LoadModule(client: BotClient, moduleName: string) {
	const fileUrl = pathToFileURL(path.join(import.meta.dirname, "..", "Modules", moduleName)).href + ".ts?t=" + Date.now();
	const newModule = (await import(fileUrl)).default as ModuleInterface;
	if (newModule.load as unknown && newModule.unload as unknown) {
		client.modules.set(moduleName, newModule);
		newModule.load(client);
	} else {
		throw new TypeError(`Module ${moduleName} is missing a required "load" or "unload" function.`);
	}
}
