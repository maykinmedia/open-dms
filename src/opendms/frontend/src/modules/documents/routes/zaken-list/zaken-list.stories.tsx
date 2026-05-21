import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { expect, userEvent, within } from "storybook/test";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
  MOCK_ZAKEN,
} from "../../../../../.storybook/mocks.ts";
import {
  sanitizedReactRouterParameters,
  waitForIdle,
  waitForLoading,
} from "../../../../../.storybook/utils.ts";
import { ZakenList } from "./zaken-list.tsx";

initialize();

const meta: Meta<typeof ZakenList> = {
  title: "Routes/Zaken",
  component: ZakenList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZakenList>;

export const Fallback: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/documenten/"),
  },
};

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/documenten/service_2/22222222-2222-2222-2222-222222222222/2023",
    ),
    msw: {
      handlers: [
        MOCK_SERVICE_OPTIONS,
        MOCK_ZAAKTYPE_OPTIONS,
        MOCK_ZAAKTYPE,
        MOCK_ZAKEN,
      ],
    },
  },
  play: async ({ canvasElement }) => {
    // Controls
    const identificatie =
      await within(canvasElement).findByPlaceholderText("Identificatie");
    const omschrijving =
      await within(canvasElement).findByPlaceholderText("Omschrijving");
    const page = await within(canvasElement).findByLabelText("Page");
    const nextPage = await within(canvasElement).findByRole("button", {
      name: /Go to next page/,
    });

    // Navigate to page 3
    await userEvent.click(nextPage);
    await userEvent.click(nextPage);

    // Wait for update
    await waitForLoading(canvasElement);
    await waitForIdle(canvasElement);

    // Test that:
    // - we have navigated to page 3
    // - we have made the correct (msw) request for page 3
    const [, , ...rows1] = await within(canvasElement).findAllByRole("row");
    expect(page).toHaveValue(3); // UI only
    expect(rows1[0].children[0].textContent).toBe("zaak-201");

    // Filter
    await userEvent.type(identificatie, "zaak-10");
    await userEvent.type(omschrijving, "lorem");

    // Wait for update
    await waitForLoading(canvasElement);
    await waitForIdle(canvasElement);

    // Test that:
    // - we have navigated back to page 1
    // - we have made the correct (msw) request for the filters
    const [, , ...rows2] = await within(canvasElement).findAllByRole("row");
    expect(page).toHaveValue(1); // UI only
    expect(rows2[0].children[0].textContent).toBe("zaak-10");
    expect(rows2[1].children[0].textContent).toBe("zaak-100");
  },
};
