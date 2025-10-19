import { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../command-interface.ts";

const command: CommandInterface = {
	data: new SlashCommandBuilder().setName("ping").setDescription("ping pong!"),
	async execute(interaction: ChatInputCommandInteraction) {
		await interaction.reply("Ping!");
	},
};

export default command;