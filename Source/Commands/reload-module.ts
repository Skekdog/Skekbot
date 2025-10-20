import { ChatInputCommandInteraction, MessageFlags, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";
import { isBotClient } from "../bot-client.ts";
import { pathToFileURL } from "url";
import path from "path";
import type { ModuleInterface } from "../Types/module-interface.ts";

const command: CommandInterface = {
	isDevServer: true,

	data: new SlashCommandBuilder().setName("reload-module").setDescription("Reloads a module.")
		.addStringOption(option => option.setName("module").setDescription("The module to reload.").setRequired(true)) as SlashCommandBuilder,

	async execute(interaction: ChatInputCommandInteraction) {
		if (!isBotClient(interaction.client)) throw new Error("Interaction client is not a BotClient.");

		const moduleOption = interaction.options.get("module");
		if (!moduleOption) {
			await interaction.reply({
				content: "Missing module argument.",
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		let moduleName = moduleOption.value;
		if (typeof moduleName !== "string") {
			await interaction.reply({
				content: "Invalid module argument, expected string, received " + typeof moduleName,
				flags: MessageFlags.Ephemeral,
			});
			return;
		}

		moduleName = moduleName.toLowerCase();

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
			const fileUrl = pathToFileURL(path.join(import.meta.dirname, "..", "Modules", moduleName)).href + ".ts?t=" + Date.now();
			const newModule = (await import(fileUrl)).default as ModuleInterface;
			if (newModule.load as unknown && newModule.unload as unknown) {
				interaction.client.modules.set(moduleName, newModule);
				newModule.load(interaction.client);
				await interaction.reply(`Module ${moduleName} reloaded.`);
			} else {
				await interaction.reply(`Module ${moduleName} is missing required "load" or "unload" functions.`);
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
