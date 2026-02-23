// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import { ignoreBuildArtifacts } from "@maykinmedia/eslint-config";
import maykin from "@maykinmedia/eslint-config/recommended";

const config = [ignoreBuildArtifacts(["build"]), {
  ignores: ["dist"],
}, ...maykin, {
  rules: {
    "react-hooks/exhaustive-deps": "off",
  },
}, ...storybook.configs["flat/recommended"]];

export default config;
