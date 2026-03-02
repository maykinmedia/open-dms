import { Hr, Sidebar, Toolbar } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { HttpResponse, http } from "msw";
import { initialize, mswLoader } from "msw-storybook-addon";
import {
  reactRouterParameters,
  withRouter,
} from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect, ZaaktypeSelect } from "~/components";

initialize();

const MOCK_SERVICE_OPTIONS = http.get("/api/v1/services", () =>
  HttpResponse.json({
    results: [
      { label: "Service 1", slug: "service_1" },
      { label: "Service 2", slug: "service_2" },
    ],
  }),
);

const MOCK_ZAAKTYPE_OPTIONS = http.get(
  "/api/v1/services/:serviceSlug/zaaktypen",
  () =>
    HttpResponse.json({
      results: [
        { label: "Zaaktype 1", slug: "zaaktype_1" },
        { label: "Zaaktype 2", slug: "zaaktype_2" },
      ],
    }),
);

const meta: Meta<typeof ZaaktypeSelect> = {
  title: "Routes/ZaaktypeSelect",
  component: ZaaktypeSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: reactRouterParameters({
      routing: { path: "/:serviceSlug?/:zaaktypeSlug?" },
    }),
  },
  render: () => (
    <Sidebar>
      <Toolbar direction="v" pad={true}>
        <ServiceSelect />
        <Hr />
        <ZaaktypeSelect />
      </Toolbar>
    </Sidebar>
  ),
};

export default meta;

type Story = StoryObj<typeof ZaaktypeSelect>;

export const SelectZaaktype: Story = {
  parameters: {
    msw: { handlers: [MOCK_SERVICE_OPTIONS, MOCK_ZAAKTYPE_OPTIONS] },
  },
  play: async ({ canvasElement }) => {
    // Service
    const serviceSelect =
      await within(canvasElement).findByText("Selecteer service");

    await userEvent.click(serviceSelect);

    const searchInput1 =
      await within(canvasElement).findByPlaceholderText("Zoeken");

    await userEvent.type(searchInput1, "service");

    const optionService2 = await within(canvasElement).findByText("Service 2");

    await userEvent.click(optionService2);

    // Zaaktype
    const zaaktypeSelect =
      await within(canvasElement).findByText("Selecteer zaaktype");

    await userEvent.click(zaaktypeSelect);

    const searchInput2 =
      await within(canvasElement).findByPlaceholderText("Zoeken");

    await userEvent.type(searchInput2, "service");

    const optionZaaktype2 =
      await within(canvasElement).findByText("Zaaktype 2");

    await userEvent.click(optionZaaktype2);
  },
};
