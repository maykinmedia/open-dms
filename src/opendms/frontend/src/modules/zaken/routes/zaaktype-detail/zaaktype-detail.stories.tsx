import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_CREATE_STATUS,
  MOCK_CREATE_ZAAK,
  MOCK_SERVICE_OPTIONS,
  MOCK_STATUSTYPEN,
  MOCK_ZAAKTYPE,
  MOCK_ZAKEN_WITH_STATUS,
} from "../../../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../../../.storybook/utils.ts";
import { ZaaktypeDetail } from "./zaaktype-detail.tsx";

initialize();

const meta: Meta<typeof ZaaktypeDetail> = {
  title: "Modules/Zaken/Routes/ZaaktypeDetail",
  component: ZaaktypeDetail,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZaaktypeDetail>;

export const Kanban: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/zaken/service_2/zaaktypen/22222222-2222-2222-2222-222222222222",
    ),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_ZAAKTYPE,
        MOCK_STATUSTYPEN,
        MOCK_ZAKEN_WITH_STATUS,
        MOCK_CREATE_STATUS,
        MOCK_CREATE_ZAAK,
      ],
    },
  },
};
