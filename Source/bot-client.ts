import { ChatInputCommandInteraction, Client, Collection, SlashCommandBuilder } from "discord.js";

export class BotClient extends Client {
	commands: Collection<string, { data: SlashCommandBuilder, execute: (interaction: ChatInputCommandInteraction) => Promise<void>}> = new Collection();
}