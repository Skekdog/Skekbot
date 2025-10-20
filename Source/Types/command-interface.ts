import type { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";

export interface CommandInterface {
	isDevServer?: boolean,
	data: SlashCommandBuilder,
	execute(interaction: ChatInputCommandInteraction): Promise<void>
}
