import type { BotClient } from "../bot-client.ts";
import { promises as fsPromises } from "fs";
import path from "path";
import { Collection } from "discord.js";
import LoadModule from "./load-module.ts";

export default async function LoadModules(client: BotClient) {
	client.modules = new Collection();

	const moduleFolderPath = path.join(import.meta.dirname, "..", "Modules");

	for await (const entry of fsPromises.glob("**/*.ts", { cwd: moduleFolderPath })) {
		await LoadModule(client, path.basename(entry, ".ts"));
	}
}
