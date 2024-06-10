require("dotenv").config();

const eris = require("eris");
const axios = require("axios");
const config = require("./modules/config");
const { getLogsChannel } = require("./modules/utils");

const bot = new eris.CommandClient(
	process.env.BOT_TOKEN,
	{ intents: ["guildMessages", "guilds"] },
	{ prefix: config.PREFIX }
);

async function checkHateSpeech(message) {
	console.log("Checking hate speech");
	try {
		// Call the API here
		console.log(message);
		const response = await axios.post(process.env.API_ENDPOINT, {
			sentence: message.content,
		});
		const result = response.data;
		console.log(result);

		const logsChannel = getLogsChannel(message);

		if (result.values.normal < 0.5) {
			// Delete the message
			message.delete();
			// Warn the user
			message.channel.createMessage(
				`${message.author.mention} You have been warned for sending hateful content.`
			);
			// Create a lgo message for deletion
			logsChannel.createMessage({
				embed: {
					color: commandHandler.dangerColor,
					author: {
						name: message.author.username,
						icon_url: message.author.staticAvatarURL,
					},
					title: `:exclamation: Message deleted for hate speech`,
					description: message.content,
				},
			});
			return;
		} else if (result.values.normal < 0.75) {
			logsChannel.createMessage({
				embed: {
					color: commandHandler.warningColor,
					author: {
						name: message.author.username,
						icon_url: message.author.staticAvatarURL,
					},
					title: `:warning: Potential Hate Speech`,
					description: `[Jump!](${message.jumpLink})\n\n${message.content}`,
				},
			});
			return;
		}
	} catch (error) {
		console.log(error);
	}
}

bot.on("ready", async () => {
	console.log("Connected and ready.");
});

bot.on("messageCreate", async (msg) => {
	if (msg.author != bot.user) {
		checkHateSpeech(msg);
	}

	const botWasMentioned = msg.mentions.find(
		(mentionedUser) => mentionedUser.id === bot.user.id
	);

	if (botWasMentioned) {
		try {
			await msg.channel.createMessage({
				content: `Hey there!`,
				messageReferenceID: msg.id,
			});
		} catch (err) {
			// There are various reasons why sending a message may fail.
			// The API might time out or choke and return a 5xx status,
			// or the bot may not have permission to send the
			// message (403 status).
			console.warn("Failed to respond to mention.");
			console.warn(err);
		}
	}
});

bot.on("error", (err) => {
	console.warn(err);
});

bot.on("messageUpdate", async (message, oldMessage) => {
	checkHateSpeech(message);

	if (oldMessage == null) {
		console.warn("Couldn't get complete data about event");
		return;
	}
	console.log(message, oldMessage);

	const logsChannel = getLogsChannel(message);
	await logsChannel.createMessage({
		embed: {
			color: commandHandler.embedColor,
			author: {
				name: message.author.username,
				icon_url: message.author.staticAvatarURL,
			},
			title: "Message Edited",
			description: `[Jump!](${message.jumpLink})`,
			fields: [
				{ name: "Before :", value: oldMessage?.content || "null" },
				{ name: "After :", value: message?.content || "null" },
			],
		},
	});
});

bot.connect();
