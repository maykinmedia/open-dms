import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import { sanitizedReactRouterParameters } from "../../../../../.storybook/utils.ts";
import { ZakenFallback } from "./zaken-fallback.tsx";

initialize();

const meta: Meta<typeof ZakenFallback> = {
  title: "Modules/Zaken/Routes/Zaaktypen",
  component: ZakenFallback,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZakenFallback>;

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/zaken/service_2/zaaktypen"),
  },
};
