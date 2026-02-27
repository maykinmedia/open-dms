// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import { ignoreBuildArtifacts } from "@maykinmedia/eslint-config";
import maykin from "@maykinmedia/eslint-config/recommended";

const config = [
  ignoreBuildArtifacts(["build"]),
  {
    ignores: ["dist", "src/types/schema.d.ts "],
  },
  ...maykin,
  {
    rules: {
      "react-hooks/exhaustive-deps": "off",
    },
  },
];

export default config;
