import client from "../client.ts";
import * as z from "zod/v4";
import { env } from "../Utility/env.ts";
import { Elysia, status } from "elysia";
import { staticPlugin } from "@elysiajs/static";
import { bearer as bearerAuth } from "@elysiajs/bearer";

const password = env.WEB_PASSWORD!;

const PORT = env.PORT;

const MessageRequest = z.object({
	channelId: z.string(),
	message: z.string(),
	replyToId: z.string(),
});

const app = new Elysia()
	.get("/", "BLANK PAGE.")
	.get("/status", async () => {
		const clientReady = client.isReady();

		return {
			client: clientReady
		};
	})
	.use(bearerAuth())
	.use(
		await staticPlugin({
			assets: "./Source/Web/Static",
			prefix: "/",
		})
	)
	.post(
		"/send-message",
		async ({ bearer, body }) => {
			if (!bearer) return status(401, "Unauthorized");

			if (bearer !== password) return status(403, "Forbidden");

			const channel = await client.channels.fetch(body.channelId);
			if (!channel || !channel.isSendable()) return status(400, "Invalid channel");

			const replyToMessage = body.replyToId
				? await channel.messages.fetch(body.replyToId)
				: undefined;

			if (replyToMessage) {
				replyToMessage.reply(body.message);
			} else {
				channel.send(body.message);
			}

			return "Success!";
		},
		{
			body: MessageRequest,
		}
	)
	.listen(PORT);

export type App = typeof app;

console.log(`Web interface starting on port ${app.server?.hostname}:${app.server?.port}`);
