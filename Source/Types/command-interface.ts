import type { ChatInputCommandInteraction, SlashCommandOptionsOnlyBuilder } from "discord.js";

export interface CommandInterface {
	isDevServer?: boolean,
	data: SlashCommandOptionsOnlyBuilder,
	execute(interaction: ChatInputCommandInteraction): Promise<void>
}
