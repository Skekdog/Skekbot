import { ActionRowBuilder, ButtonBuilder, ButtonInteraction, ButtonStyle, ComponentType, SlashCommandBuilder, User } from "discord.js";
import type { CommandInterface } from "../Types/command-interface.ts";

const options = {
	Rock: "🪨",
	Paper: "📄",
	Scissors: "✂️",
};

async function announce(buttonInteraction: ButtonInteraction, user1: User, user2: User, user1Choice: string, user2Choice: string) {
	let outcome;

	if (user1Choice === user2Choice) {
		outcome = user1 === user2 ? "You played yourself and tied!" : "It's a tie!";
	} else if (
		(user1Choice === "Rock" && user2Choice === "Scissors") ||
		(user1Choice === "Scissors" && user2Choice === "Paper") ||
		(user1Choice === "Paper" && user2Choice === "Rock") )
	{
		outcome = user1 === user2 ? "You played yourself and won!" : `${user1} wins!`;
	} else {
		outcome = user1 === user2 ? "You played yourself and lost!" : `${user2} wins!`;
	}

	await buttonInteraction.reply({
		content: `${user1} chose ${user1Choice}.\n${user2} chose ${user2Choice}.\n\n${outcome}`,
	});
}

const command: CommandInterface = {
	data: new SlashCommandBuilder()
		.setName("rock-paper-scissors")
		.setDescription("Play a game of rock paper scissors.")
		.addUserOption(option => option
			.setName("against")
			.setDescription("The user to play against. Defaults to the bot.")
		),

	async execute(interaction) {
		const against = interaction.options.getUser("against") ?? interaction.client.user;
		const initiator = interaction.user;

		const row = new ActionRowBuilder<ButtonBuilder>();

		for (const [key, value] of Object.entries(options)) {
			row.addComponents(new ButtonBuilder()
				.setCustomId(key)
				.setLabel(key)
				.setEmoji(value)
				.setStyle(ButtonStyle.Primary));
		}

		const response = await interaction.reply({
			content: `${against}, ${initiator} has challenged you to a game of rock paper scissors!`,
			components: [row],
			withResponse: true,
		});

		const collector = response.resource?.message?.createMessageComponentCollector({
			componentType: ComponentType.Button,
			filter: buttonInteraction => buttonInteraction.user.id === initiator.id || buttonInteraction.user.id === against.id,
		});

		if (!collector) {
			await interaction.editReply({
				content: "An error occurred.",
			});
			return;
		}

		let user1Choice: string | undefined;
		let user2Choice: string | undefined;

		collector.on("collect", async buttonInteraction => {
			const id = buttonInteraction.customId;
			const user = buttonInteraction.user;

			if (user === initiator) user1Choice = id;
			else if (user === against) user2Choice = id;

			if (against.bot || against === user) {
				const botChoice = Object.keys(options)[Math.floor(Math.random() * Object.keys(options).length)];
				if (typeof botChoice !== "string") throw new Error("Bot choice is not a string.");

				user2Choice = botChoice;
			}

			if (user1Choice && user2Choice) {
				collector.stop();
				await announce(buttonInteraction, initiator, against, user1Choice, user2Choice);
				return;
			}

			await buttonInteraction.deferUpdate();
		});
	}
};

export default command;
