import Bun from "bun";

export const env = {
	BOT_TOKEN: Bun.env["BOT_ID"],
	PORT: Number.parseInt(Bun.env["PORT"] ?? "443"),
	WEB_PASSWORD: Bun.env["WEB_PASSWORD"],
	DEV_SERVER_ID: Bun.env["DEV_SERVER_ID"], // note: this is a string, due to discord.js
};
