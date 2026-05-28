import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";

import { withCSRF } from "../../../../../.storybook/decorators.tsx";
import {
  MOCK_CREATE_ZAAK,
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAK_DETAIL,
  MOCK_ZAAKTYPE,
  MOCK_ZAAKTYPE_OPTIONS,
  MOCK_ZAKEN_FOR_ZAAKTYPE,
} from "../../../../../.storybook/mocks.ts";
import {
  sanitizedReactRouterParameters,
  waitForIdle,
} from "../../../../../.storybook/utils.ts";
import { ZakenList } from "./zaken-list.tsx";

initialize();

const meta: Meta<typeof ZakenList> = {
  title: "Modules/Zaken/Routes/ZakenList",
  component: ZakenList,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
};

export default meta;

type Story = StoryObj<typeof ZakenList>;

const BASE_HANDLERS = [
  MOCK_SERVICE_OPTIONS,
  MOCK_ZAAKTYPE_OPTIONS,
  MOCK_ZAAKTYPE,
  MOCK_ZAKEN_FOR_ZAAKTYPE,
];

export const List: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/zaken/service_2/22222222-2222-2222-2222-222222222222",
    ),
    msw: { handlers: BASE_HANDLERS },
  },
};

export const CreateZaak: Story = {
  parameters: {
    reactRouter: sanitizedReactRouterParameters(
      "/zaken/service_2/22222222-2222-2222-2222-222222222222",
    ),
    msw: {
      handlers: [...BASE_HANDLERS, MOCK_CREATE_ZAAK, MOCK_ZAAK_DETAIL],
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    const createButton = await canvas.findByRole("button", {
      name: /Zaak aanmaken/,
    });
    await userEvent.click(createButton);

    const modal = within(document.body);
    const omschrijvingInput = await modal.findByLabelText("Omschrijving");
    const startdatumInput = await modal.findByLabelText("Startdatum");

    await userEvent.type(omschrijvingInput, "Nieuwe zaak omschrijving");
    await userEvent.type(startdatumInput, "2023-06-15");

    const submitButton = await modal.findByRole("button", {
      name: "Aanmaken",
    });
    await userEvent.click(submitButton);

    await waitForIdle(canvasElement);
  },
};
