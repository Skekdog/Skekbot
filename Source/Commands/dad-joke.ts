import { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";
import * as z from "zod/v4";

const dadJokeResponse = z.object({
	joke: z.string(),
});

const command: CommandInterface = {
	data: new SlashCommandBuilder()
		.setName("dad-joke")
		.setDescription("gives a (not) very funny dad joke."),

	async execute(interaction: ChatInputCommandInteraction) {
		const res = await fetch("https://api.gurkz.me/api/dad-joke");

		const json = await res.json();

		const parseResult = await dadJokeResponse.safeParseAsync(json);

		if (!parseResult.success) {
			console.error(parseResult.error);
			await interaction.reply("the dad joke was so bad it failed to run");
			return;
		}

		await interaction.reply(`here's one for you: ${parseResult.data.joke}`);
	},
};

export default command;
