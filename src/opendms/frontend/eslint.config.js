import { ignoreBuildArtifacts } from "@maykinmedia/eslint-config";
import maykin from "@maykinmedia/eslint-config/recommended";

const config = [
  ignoreBuildArtifacts(["build"]),
  {
    ignores: ["dist"],
  },
  ...maykin,
  {
    rules: {
      "react-hooks/exhaustive-deps": "off",
    },
  },
];

export default config;
