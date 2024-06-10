function getLogsChannel(message) {
	// Retrieve the guild object
	const guild = bot.guilds.get(message.guildID);

	// Find the channel with the name "logs"
	const logsChannel = guild.channels.find((channel) =>
		channel.name.startsWith("logs")
	);

	return logsChannel;
}

module.exports = {
	getLogsChannel,
};
