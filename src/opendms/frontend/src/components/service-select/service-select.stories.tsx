import type { Meta, StoryObj } from "@storybook/react-vite";
import { HttpResponse, http } from "msw";
import { initialize, mswLoader } from "msw-storybook-addon";
import {
  reactRouterParameters,
  withRouter,
} from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect } from "~/components";

initialize();

const MOCK_SERVICE_OPTIONS = http.get("/api/v1/services", () =>
  HttpResponse.json({
    results: [
      { label: "Service 1", slug: "service_1" },
      { label: "Service 2", slug: "service_2" },
    ],
  }),
);

const meta: Meta<typeof ServiceSelect> = {
  title: "Context/ServiceSelect",
  component: ServiceSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: reactRouterParameters({
      routing: { path: "/:serviceSlug?" },
    }),
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
