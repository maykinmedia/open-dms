import type { Meta, StoryObj } from "@storybook/react-vite";
import {
  reactRouterParameters,
  withRouter,
} from "storybook-addon-remix-react-router";
import { userEvent } from "storybook/test";
import { ServiceSelect } from "~/components/service-select/service-select.tsx";

import { withCSRF } from "../../../.storybook/decorators.tsx";

const meta: Meta<typeof ServiceSelect> = {
  title: "Routes/ServiceSelect",
  component: ServiceSelect,
  decorators: [withRouter, withCSRF],
  args: {
    options: [
      {
        label: "Option 1",
        value: "option 1",
      },
      {
        label: "Option 2",
        value: "option 2",
      },
    ],
  },
};

export default meta;

type Story = StoryObj<typeof ServiceSelect>;

export const SelectService: Story = {
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
