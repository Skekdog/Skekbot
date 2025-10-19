export default function(user: string) {
	return user === process.env["DEVELOPER_ID"];
}