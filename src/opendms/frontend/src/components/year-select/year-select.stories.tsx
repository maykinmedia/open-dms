import { Sidebar, Toolbar } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect, YearSelect, ZaaktypeSelect } from "~/components";

import {
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
} from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";

initialize();

const meta: Meta<typeof YearSelect> = {
  title: "Context",
  component: YearSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
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
