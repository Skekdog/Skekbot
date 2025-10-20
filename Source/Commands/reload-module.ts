import { ChatInputCommandInteraction, MessageFlags, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";
import { isBotClient } from "../bot-client.ts";
import LoadModule from "../Load/load-module.ts";

const command: CommandInterface = {
	isDevServer: true,

	data: new SlashCommandBuilder().setName("reload-module").setDescription("Reloads a module.")
		.addStringOption(option => option.setName("module").setDescription("The module to reload.").setRequired(true)) as SlashCommandBuilder,

	async execute(interaction: ChatInputCommandInteraction) {
		if (!isBotClient(interaction.client)) throw new Error("Interaction client is not a BotClient.");

		const moduleName = interaction.options.getString("module")?.toLowerCase() ?? "";

		const foundModule = interaction.client.modules.get(moduleName);
		if (!foundModule) {
			await interaction.reply({
				content: `Module ${moduleName} not found.`,
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		foundModule.unload(interaction.client);

		try {
			await LoadModule(interaction.client, moduleName);
			await interaction.reply(`Module ${moduleName} reloaded.`);
		} catch (error) {
			await interaction.reply({
				content: `An error occurred: ${error}`,
				flags: MessageFlags.Ephemeral,
			});
		}
	},
};

export default command;
