/**
 * Prettier configuration shared across the workspace.
 * Placed under configs/ to align with other tooling settings.
 * @type {import("prettier").Config}
 */

export default {
  printWidth: 100,
  semi: true,
  singleQuote: false,
  trailingComma: "all",
  tabWidth: 2,
  useTabs: false,
  overrides: [
    {
      files: ["*.md"],
      options: {
        proseWrap: "always",
      },
    },
  ],
};
