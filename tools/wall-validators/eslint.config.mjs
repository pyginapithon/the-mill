/** JS parse plus rules that catch impossible code. No style rules. */
export default [
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
    },
    rules: {
      "no-const-assign": "error",
      "no-constant-binary-expression": "error",
      "no-dupe-args": "error",
      "no-dupe-else-if": "error",
      "no-dupe-keys": "error",
      "no-duplicate-case": "error",
      "no-import-assign": "error",
      "no-obj-calls": "error",
      "no-self-assign": "error",
      "no-setter-return": "error",
      "no-unreachable": "error",
      "no-unsafe-finally": "error",
      "no-unsafe-negation": "error",
      "use-isnan": "error",
      "valid-typeof": "error",
    },
  },
];
