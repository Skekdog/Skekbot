import { CommandInteraction, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../command-interface.ts";

const command: CommandInterface = {
	data: new SlashCommandBuilder().setName("ping").setDescription("ping pong!"),
	async execute(interaction: CommandInteraction) {
		await interaction.reply("Pong!");
	},
};

export default command;