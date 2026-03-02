import { Sidebar, Toolbar } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { HttpResponse, http } from "msw";
import { initialize, mswLoader } from "msw-storybook-addon";
import {
  reactRouterParameters,
  withRouter,
} from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect, YearSelect, ZaaktypeSelect } from "~/components";
import type { ZaakType } from "~/types";

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
        {
          identificatie: "Zaaktype 1",
          uuid: "11111111-1111-1111-1111-111111111111",
        },
        {
          identificatie: "Zaaktype 2",
          uuid: "22222222-2222-2222-2222-222222222222",
        },
      ],
    }),
);

const MOCK_ZAAKTYPE = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222",
  () =>
    HttpResponse.json({
      identificatie: "Zaaktype 2",
      uuid: "22222222-2222-2222-2222-222222222222",
      beginGeldigheid: "01-01-2020",
      eindeGeldigheid: "01-01-2026",
    } as Partial<ZaakType>),
);

const meta: Meta<typeof YearSelect> = {
  title: "Context/YearSelect",
  component: YearSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: reactRouterParameters({
      routing: { path: "/:serviceSlug?/:zaaktypeUuid?/:zaakYear?" },
    }),
  },
  render: () => (
    <Sidebar>
      <Toolbar direction="v" pad={true} align="space-between">
        <ServiceSelect />
        <ZaaktypeSelect />
        <YearSelect />
      </Toolbar>
    </Sidebar>
  ),
};

export default meta;

type Story = StoryObj<typeof YearSelect>;

export const SelectYear: Story = {
  parameters: {
    msw: {
      handlers: [MOCK_SERVICE_OPTIONS, MOCK_ZAAKTYPE_OPTIONS, MOCK_ZAAKTYPE],
    },
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
    const yearSelect =
      await within(canvasElement).findByText("Selecteer zaaktype");

    await userEvent.click(yearSelect);

    const searchInput2 =
      await within(canvasElement).findByPlaceholderText("Zoeken");

    await userEvent.type(searchInput2, "service");

    const optionZaaktype2 =
      await within(canvasElement).findByText("Zaaktype 2");

    await userEvent.click(optionZaaktype2);

    // Year
    const button2023 = await within(canvasElement).findByText("2023");

    await userEvent.click(button2023);
  },
};
