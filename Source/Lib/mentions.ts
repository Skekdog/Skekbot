/**
 * removes all mention patterns from a message
 * @param input unparsed message
 * @returns message without the mentions
 */
export function removeMentions(input: string): string {
	return input.replace(/<@!?\d+>|<@&\d+>|<#\d+>|@everyone|@here/g, "");
}

/**
 * changes the @ to prevent mentions
 * @param input unparsed message
 * @returns sanitised message
 */
export function sanitiseMentions(input: string): string {
	return input.replace(/@/g, "@​");
}
