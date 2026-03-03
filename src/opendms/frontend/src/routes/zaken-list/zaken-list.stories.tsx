import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../.storybook/decorators.tsx";
import {
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
  MOCK_ZAKEN,
} from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";
import { ZakenList } from "./zaken-list.tsx";

initialize();

const meta: Meta<typeof ZakenList> = {
  title: "Routes/Zaken",
  component: ZakenList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZakenList>;

export const Fallback: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
  },
};

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/service_2/22222222-2222-2222-2222-222222222222/2023",
    ),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_ZAAKTYPE_OPTIONS,
        MOCK_ZAAKTYPE,
        MOCK_ZAKEN,
      ],
    },
  },
};
