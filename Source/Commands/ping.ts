import { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";

const command: CommandInterface = {
	data: new SlashCommandBuilder().setName("ping").setDescription("ping pong!"),
	async execute(interaction: ChatInputCommandInteraction) {
		await interaction.reply("Pong!");
	},
};

export default command;