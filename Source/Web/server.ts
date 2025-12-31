import { Hono } from "hono";
import client from "../client.ts";
import * as z from "zod/v4";
import { prettyJSON } from "hono/pretty-json";
import { serveStatic } from "@hono/node-server/serve-static";
import { bearerAuth } from "hono/bearer-auth";
import { serve } from "@hono/node-server";
import { zValidator } from "@hono/zod-validator";
import { env } from "../Utility/env.ts";

const password = env.WEB_PASSWORD!;

const PORT = env.PORT;

const app = new Hono();

const MessageRequest = z.object({
	channelId: z.string(),
	message: z.string(),
	replyToId: z.string(),
});

app.use(prettyJSON());

app.get("/", (c) => {
	return c.text("BLANK PAGE.");
});

app.use(
	"*",
	serveStatic({
		root: "Source/Web/Page",
		rewriteRequestPath: (path) => {
			// if the path already has an extension, leave it alone
			if (path.includes(".")) {
				return path;
			}

			// if not, try serving `<path>.html`
			return `${path}.html`;
		},
	})
);

app
	.use(bearerAuth({ token: password }))
	.post("/send-message", zValidator("json", MessageRequest), async (c) => {
		const messageRequest = c.req.valid("json");

		const channel = await client.channels.fetch(messageRequest.channelId);
		if (!channel || !channel.isSendable()) throw new Error("Bad channel");

		const replyToMessage = messageRequest.replyToId
			? await channel.messages.fetch(messageRequest.replyToId)
			: undefined;

		if (replyToMessage) {
			replyToMessage.reply(messageRequest.message);
		} else {
			channel.send(messageRequest.message);
		}

		return c.text("Success!");
	});

const server = serve({
	port: PORT,
	fetch: app.fetch,
});

server.addListener("listening", () => {
	console.log(`Web interface starting on port ${PORT}.`);
});
