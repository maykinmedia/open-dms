import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
  MOCK_ZAAK_DETAIL,
} from "../../../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../../../.storybook/utils.ts";
import { ZaakDetail } from "./zaak-detail.tsx";

initialize();

const meta: Meta<typeof ZaakDetail> = {
  title: "Modules/Zaken/Routes/ZaakDetail",
  component: ZaakDetail,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZaakDetail>;

export const Detail: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/zaken/service_2/22222222-2222-2222-2222-222222222222/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    ),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_ZAAKTYPE_OPTIONS,
        MOCK_ZAAKTYPE,
        MOCK_ZAAK_DETAIL,
      ],
    },
  },
};
