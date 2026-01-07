import { treaty } from "@elysiajs/eden";
import type { App } from "../../Source";

const messageArea = document.getElementById(
	"message-box"
) as HTMLTextAreaElement | null;
const sendButton = document.getElementById(
	"message-button"
) as HTMLButtonElement | null;
const channelInput = document.getElementById(
	"channel-input"
) as HTMLInputElement | null;
const replyInput = document.getElementById(
	"reply-input"
) as HTMLInputElement | null;
const passwordInput = document.getElementById(
	"password-input"
) as HTMLInputElement | null;

if (
	!messageArea ||
	!sendButton ||
	!channelInput ||
	!replyInput ||
	!passwordInput
) {
	throw new Error("required DOM elements are missing");
}

const app = treaty<App>("/");

sendButton.addEventListener("click", async (event: MouseEvent) => {
	event.preventDefault();

	if (!channelInput.value || !messageArea.value || !passwordInput.value) {
		alert("channel, message, and password are required.");
		return;
	}

	sendButton.disabled = true;
	sendButton.setAttribute("aria-busy", "true");

	try {
		const res = await app["send-message"].post(
			{
				channelId: channelInput.value,
				message: messageArea.value,
				replyToId: replyInput.value || "",
			},
			{
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${passwordInput.value}`,
				},
			}
		);

		if (res.error) {
			throw new Error(res.error.value);
		}

		const text: string = await res.data;
		alert(text);

		messageArea.value = "";
		replyInput.value = "";
	} catch (err) {
		console.error(err);
		alert("failed to send message");
	} finally {
		sendButton.disabled = false;
		sendButton.setAttribute("aria-busy", "false");
	}
});
