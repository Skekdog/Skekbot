import express from "express";
import client from "../client.ts";
import * as z from "zod";

const WEB_PASSWORD = process.env["WEB_PASSWORD"];

function authenticatedRoute(
	req: express.Request,
	res: express.Response,
	next: express.NextFunction
) {
	if (req.headers.authorization !== `Bearer ${WEB_PASSWORD}`) {
		return res.status(401).send({ message: "invalid key" });
	}

	return next();
}

const PORT = 443;

const app = express();

const MessageRequest = z.object({
	channelId: z.string(),
	message: z.string(),
	replyToId: z.string(),
});

app.use(express.json());

app.get("/", (_, res) => {
	res.send("BLANK PAGE.");
});

app.use(
	express.static("Source/Web/Page", {
		extensions: ["html"],
	})
);

app.use(authenticatedRoute).post("/send-message", async (req, res) => {
	const messageRequest = MessageRequest.parse(req.body);

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

	res.send("Success!");
});

app.listen(PORT, () => {
	console.log(`Web interface starting on port ${PORT}.`);
});
