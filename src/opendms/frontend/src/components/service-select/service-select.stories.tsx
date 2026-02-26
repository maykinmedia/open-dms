import type { LoadOptionsFn } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { HttpResponse, http } from "msw";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent } from "storybook/test";
import { ServiceSelect } from "~/components/service-select/service-select.tsx";

import { withCSRF } from "../../../.storybook/decorators.tsx";

initialize();

const loadOptions: LoadOptionsFn = async () => {
  const res = await fetch("/api/v1/services", { method: "POST" });
  return res.json();
};

const MOCK_SERVICE_OPTIONS = http.post("/api/v1/services", () =>
  HttpResponse.json([
    { label: "Option 1", value: "option 1" },
    { label: "Option 2", value: "option 2" },
  ]),
);

const meta: Meta<typeof ServiceSelect> = {
  title: "Routes/ServiceSelect",
  component: ServiceSelect,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  args: {
    options: loadOptions,
  },
};

export default meta;

type Story = StoryObj<typeof ServiceSelect>;

export const SelectService: Story = {
  parameters: { msw: { handlers: [MOCK_SERVICE_OPTIONS] } },
  play: async ({ canvasElement }) => {
    const select = canvasElement.querySelector("select") as HTMLSelectElement;
    await userEvent.click(select);

    const dropdown = canvasElement.querySelector(
      ".mykn-select__options",
    ) as HTMLDivElement;

    const firstOption = dropdown.querySelector(
      ".mykn-option",
    ) as HTMLDivElement;

    await userEvent.click(firstOption);
  },
};
