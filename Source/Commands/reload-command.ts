import { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../command-interface.ts";
import { isBotClient } from "../bot-client.ts";
import { pathToFileURL } from "url";
import path from "path";

const command: CommandInterface = {
	data: new SlashCommandBuilder().setName("reload-command").setDescription("Reloads a command.")
		.addStringOption(option => option.setName("command").setDescription("The command to reload.").setRequired(true)) as SlashCommandBuilder,

	async execute(interaction: ChatInputCommandInteraction) {
		if (!isBotClient(interaction.client)) throw new Error("Interaction client is not a BotClient.");

		const commandOption = interaction.options.get("command");
		if (!commandOption) {
			await interaction.reply("An unknown error occured.");
			return;
		}

		let commandName = commandOption.value;
		if (typeof commandName !== "string") {
			await interaction.reply("An unknown error occured.");
			return;
		}

		commandName = commandName.toLowerCase();

		const foundCommand = interaction.client.commands.get(commandName);
		if (!foundCommand) {
			await interaction.reply(`Command ${commandName} not found.`);
			return;
		}

		try {
			const fileUrl = pathToFileURL(path.join(import.meta.dirname, commandName)).href + ".ts?t=" + Date.now();
			const newCommand = (await import(fileUrl)).default as CommandInterface;
			if (newCommand.data && newCommand.execute as unknown) {
				interaction.client.commands.set(commandName, newCommand);
				await interaction.reply(`Command ${commandName} reloaded.`);
			} else {
				await interaction.reply(`Command ${commandName} is missing a required "data" or "execute" property.`);
			}
		} catch (_) {
			await interaction.reply("An unknown error occured.");
		}
	},
};

export default command;