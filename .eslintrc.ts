import type { Linter } from "eslint";

const config: Linter.Config = {
	root: true,

	parser: "@typescript-eslint/parser",
	parserOptions: {
		ecmaVersion: 2025,
		sourceType: "module",
		project: "./tsconfig.json",
	},

	// @ts-ignore
	plugins: ["@typescript-eslint"],

	extends: [
		"eslint:recommended",
		"plugin:@typescript-eslint/recommended",
	],

	rules: {
		"no-unused-vars": "off",
		"@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],

		"no-shadow": "off",
		"@typescript-eslint/no-shadow": ["warn"],

		"semi": "off",
		"@typescript-eslint/semi": ["warn", "always"],

		"quotes": ["warn", "single"],
		"comma-dangle": ["warn", "only-multiline"],
		"indent": "off",
		"@typescript-eslint/indent": ["warn", 2],
	},
};

export default config;