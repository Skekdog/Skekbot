export const env = {
	BOT_TOKEN: process.env["BOT_ID"],
	PORT: Number.parseInt(process.env["PORT"] ?? "443"),
	WEB_PASSWORD: process.env["WEB_PASSWORD"],
};
