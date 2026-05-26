import { Sidebar, Toolbar } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { withCSRF } from "~/../.storybook/decorators.tsx";
import { ServiceSelect, YearSelect } from "~/components";
import { UnlinkedDocumentsButton } from "~/components/unliked-documents-button/unlinked-documents-button.tsx";

import { MOCK_SERVICE_OPTIONS } from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";

initialize();

const meta: Meta<typeof YearSelect> = {
  title: "Context",
  component: UnlinkedDocumentsButton,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/documenten/"),
  },
  render: () => (
    <Sidebar>
      <Toolbar direction="v" pad={true} align="space-between">
        <ServiceSelect />
        <UnlinkedDocumentsButton />
      </Toolbar>
    </Sidebar>
  ),
};

export default meta;

type Story = StoryObj<typeof YearSelect>;

export const SelectUnlinkedDocuments: Story = {
  parameters: {
    msw: {
      handlers: [MOCK_SERVICE_OPTIONS],
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

    throw new Error("TODO");
  },
};
