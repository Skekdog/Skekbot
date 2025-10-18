import js from "@eslint/js";
import stylistic from "@stylistic/eslint-plugin";
import globals from "globals";
import tseslint from "typescript-eslint";
import { defineConfig } from "eslint/config";

export default defineConfig([
	tseslint.configs.recommended,
	{
		files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
		plugins: {
			js,
			stylistic,
			tseslint,
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
			"no-restricted-syntax": ["error", "SwitchStatement"],

			"stylistic/indent": ["warn", "tab"],
			"stylistic/quotes": ["warn", "double", {
				"avoidEscape": true,
			}],
			"stylistic/semi": ["error", "always"],

			"@typescript-eslint/no-unused-vars": [
				"warn",
				{
					"args": "all",
					"argsIgnorePattern": "^_",
					"caughtErrors": "all",
					"caughtErrorsIgnorePattern": "^_",
					"destructuredArrayIgnorePattern": "^_",
					"varsIgnorePattern": "^_",
					"ignoreRestSiblings": true
				}
			],
			"no-unused-vars": ["off"],
		},
	},
]);
