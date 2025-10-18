import js from "@eslint/js";
import stylistic from "@stylistic/eslint-plugin"
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig } from "eslint/config";

export default defineConfig([
	{
		files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
		plugins: {
			js,
			stylistic,
		},
		extends: ["js/recommended"],
		languageOptions: {
			globals: globals.node
		},

		linterOptions: {
			reportUnusedInlineConfigs: "warn",
		},

		rules: {
			"no-duplicate-imports": "warn",
			"no-template-curly-in-string": "warn",
			"no-unassigned-vars": "warn",
			"no-use-before-define": "warn",
			"no-useless-assignment": "warn",
			"eqeqeq": "warn",
			"no-eval": "warn",
			"no-implicit-globals": "warn",
			"no-implied-eval": "warn",
			"no-invalid-this": "warn",
			"no-shadow": "warn",
			"no-unused-expressions": "warn",
			"yoda": "warn",

			"stylistic/indent": ["error", "tab"],
			"stylistic/quotes": ["warn", "double", {
				"avoidEscape": true,
			}],
		}
	},
	tseslint.configs.recommended,
]);
