import { ChatInputCommandInteraction, Collection, Events, MessageFlags, REST, Routes } from "discord.js";
import type { BotClient } from "../bot-client.ts";
import { promises as fsPromises } from "fs";
import path from "path";
import { pathToFileURL } from "url";
import type { CommandInterface } from "../Types/command-interface.ts";

async function respondToChatInteraction(client: BotClient, interaction: ChatInputCommandInteraction) {
	const command = client.commands.get(interaction.commandName);

	if (!command) throw new Error(`Unknown command ${interaction.commandName}`);

	try {
		await command.execute(interaction);
	} catch (error) {
		console.error(error);
		if (interaction.replied || interaction.deferred) {
			await interaction.followUp({
				content: "An error occurred while executing this command.",
				flags: MessageFlags.Ephemeral,
			});
			return;
		}
		await interaction.reply({
			content: "An error occurred while executing this command.",
			flags: MessageFlags.Ephemeral,
		});
	}
}

export default async function LoadCommands(client: BotClient) {
	client.commands = new Collection();

	const commandFolderPath = path.join(import.meta.dirname, "..", "Commands");

	for await (const entry of fsPromises.glob("**/*.ts", { cwd: commandFolderPath })) {
		const filePath = pathToFileURL(path.join(commandFolderPath, entry)).href;
		const command = (await import(filePath)).default as CommandInterface;
		if (command.data && command.execute as unknown) {
			client.commands.set(command.data.name, command);
		} else {
			throw new TypeError(`The command at ${filePath} is missing a required "data" or "execute" property.`);
		}
	}

	client.on(Events.InteractionCreate, async (interaction) => {
		if (interaction.isChatInputCommand()) {
			await respondToChatInteraction(client, interaction);
		}
	});

	if (!client.token) throw new Error("No token provided");
	const rest = new REST().setToken(client.token);

	if (!client.application) throw new Error("No application provided");

	try {
		console.log(`Started refreshing ${client.commands.size} application commands.`);

		const commands = client.commands.map((command) => command.data);

		await rest.put(Routes.applicationCommands(client.application.id), {
			body: commands,
		});

		console.log(`Successfully reloaded ${commands.length} application commands.`);
	} catch (error) {
		console.error(error);
	}
}