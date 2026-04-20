import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { DocumentsList } from "~/routes/documents-list/documents-list.tsx";

import { withCSRF } from "../../../.storybook/decorators.tsx";
import {
  MOCK_DOCUMENTS,
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAK,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
} from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";

initialize();

const meta: Meta<typeof DocumentsList> = {
  title: "Routes/Documents",
  component: DocumentsList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof DocumentsList>;

export const Fallback: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
  },
};

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/service_2/22222222-2222-2222-2222-222222222222/2023/123",
    ),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_ZAAKTYPE_OPTIONS,
        MOCK_ZAAKTYPE,
        MOCK_ZAAK,
        MOCK_DOCUMENTS,
      ],
    },
  },
};
