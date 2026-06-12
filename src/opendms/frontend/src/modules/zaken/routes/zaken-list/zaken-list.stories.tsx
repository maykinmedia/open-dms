import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_SERVICE_OPTIONS,
  MOCK_SERVICE_STATUS_EXPANDED_ZAKEN,
  MOCK_STATUSTYPE,
  MOCK_ZAAKTYPE,
} from "../../../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../../../.storybook/utils.ts";
import { ZakenList } from "./zaken-list.tsx";

initialize();

const meta: Meta<typeof ZakenList> = {
  title: "Modules/Zaken/Routes/Zaken",
  component: ZakenList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZakenList>;

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/zaken/service_2/zaken"),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_SERVICE_STATUS_EXPANDED_ZAKEN,
        MOCK_STATUSTYPE,
        MOCK_ZAAKTYPE,
      ],
    },
  },
};
