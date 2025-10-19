import { ChatInputCommandInteraction, MessageFlags, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";
import { isBotClient } from "../bot-client.ts";
import { pathToFileURL } from "url";
import path from "path";
import isDeveloper from "../Utility/is-developer.ts";

const command: CommandInterface = {
	data: new SlashCommandBuilder().setName("reload-command").setDescription("Reloads a command.")
		.addStringOption(option => option.setName("command").setDescription("The command to reload.").setRequired(true)) as SlashCommandBuilder,

	async execute(interaction: ChatInputCommandInteraction) {
		if (!isBotClient(interaction.client)) throw new Error("Interaction client is not a BotClient.");

		if (!isDeveloper(interaction.user.id)) {
			await interaction.reply({
				content: "You do not have permission to use this command.",
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		const commandOption = interaction.options.get("command");
		if (!commandOption) {
			await interaction.reply({
				content: "An unknown error occured.",
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		let commandName = commandOption.value;
		if (typeof commandName !== "string") {
			await interaction.reply({
				content: "An unknown error occured.",
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		commandName = commandName.toLowerCase();

		const foundCommand = interaction.client.commands.get(commandName);
		if (!foundCommand) {
			await interaction.reply({
				content: `Command ${commandName} not found.`,
				flags: MessageFlags.Ephemeral,
			});
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
			await interaction.reply({
				content: "An unknown error occured.",
				flags: MessageFlags.Ephemeral,
			});
		}
	},
};

export default command;