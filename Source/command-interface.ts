import type { CommandInteraction, SlashCommandBuilder } from "discord.js";

export interface CommandInterface {
	data: SlashCommandBuilder,
	execute(interaction: CommandInteraction): Promise<void>
}