import { ChatInputCommandInteraction, MessageFlags, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";
import { isBotClient } from "../bot-client.ts";
import LoadCommand from "../Load/load-command.ts";

const command: CommandInterface = {
	isDevServer: true,

	data: new SlashCommandBuilder().setName("reload-command").setDescription("Reloads a command.")
		.addStringOption(option => option.setName("command").setDescription("The command to reload.").setRequired(true)) as SlashCommandBuilder,

	async execute(interaction: ChatInputCommandInteraction) {
		if (!isBotClient(interaction.client)) throw new Error("Interaction client is not a BotClient.");

		const commandName = interaction.options.getString("command")?.toLowerCase() ?? "";

		const foundCommand = interaction.client.commands.get(commandName);
		if (!foundCommand) {
			await interaction.reply({
				content: `Command ${commandName} not found.`,
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		try {
			await LoadCommand(interaction.client, commandName);
			await interaction.reply(`Command ${commandName} reloaded.`);
		} catch (error) {
			await interaction.reply({
				content: `An error occurred: ${error}`,
				flags: MessageFlags.Ephemeral,
			});
		}
	},
};

export default command;
