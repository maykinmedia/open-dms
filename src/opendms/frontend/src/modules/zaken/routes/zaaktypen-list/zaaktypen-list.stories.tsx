import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPEN,
} from "../../../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../../../.storybook/utils.ts";
import { ZaaktypenList } from "./zaaktypen-list.tsx";

initialize();

const meta: Meta<typeof ZaaktypenList> = {
  title: "Modules/Zaken/Routes/Zaaktypen",
  component: ZaaktypenList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZaaktypenList>;

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/zaken/service_2/zaaktypen"),
    msw: {
      handlers: [MOCK_SERVICE_OPTIONS, MOCK_ZAAKTYPEN],
    },
  },
};
