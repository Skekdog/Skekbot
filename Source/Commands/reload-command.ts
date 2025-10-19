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

		console.log("a");

		const commandOption = interaction.options.get("command");
		if (!commandOption) {
			await interaction.reply("An unknown error occured.");
			return;
		}

		console.log("b");

		let commandName = commandOption.value;
		if (typeof commandName !== "string") {
			await interaction.reply("An unknown error occured.");
			return;
		}

		console.log("c");

		commandName = commandName.toLowerCase();

		const foundCommand = interaction.client.commands.get(commandName);
		if (!foundCommand) {
			await interaction.reply(`Command ${commandName} not found.`);
			return;
		}

		console.log("d");

		try {
			const fileUrl = pathToFileURL(path.join(import.meta.dirname, commandName)).href + ".ts?t=" + Date.now();
			const newCommand = (await import(fileUrl)).default as CommandInterface;
			console.log("r5w4r");
			if (newCommand.data && newCommand.execute as unknown) {
				interaction.client.commands.set(commandName, newCommand);
				await interaction.reply(`Command ${commandName} reloaded.`);
				console.log("e");
			} else {
				await interaction.reply(`Command ${commandName} is missing a required "data" or "execute" property.`);
				console.log("f0");
			}
		} catch (_) {
			console.log(_);
			await interaction.reply("An unknown error occured.");
		}
	},
};

export default command;