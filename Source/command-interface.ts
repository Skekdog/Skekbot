import type { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";

export interface CommandInterface {
	data: SlashCommandBuilder,
	execute(interaction: ChatInputCommandInteraction): Promise<void>
}