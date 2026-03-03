import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect } from "~/components";

import { MOCK_SERVICE_OPTIONS } from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";

initialize();

const meta: Meta<typeof ServiceSelect> = {
  title: "Context",
  component: ServiceSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
  },
};

export default meta;

type Story = StoryObj<typeof ServiceSelect>;

export const SelectService: Story = {
  parameters: { msw: { handlers: [MOCK_SERVICE_OPTIONS] } },
  play: async ({ canvasElement }) => {
    const serviceSelect =
      await within(canvasElement).findByText("Selecteer service");

    await userEvent.click(serviceSelect);

    const searchInput =
      await within(canvasElement).findByPlaceholderText("Zoeken");

    await userEvent.type(searchInput, "service");

    const optionService2 = await within(canvasElement).findByText("Service 2");

    await userEvent.click(optionService2);
  },
};
