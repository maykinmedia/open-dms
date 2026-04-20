import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";
import { GlobalSearchButton } from "~/components";

import { withCSRF } from "../../../.storybook/decorators";
import { MOCK_SEARCH } from "../../../.storybook/mocks";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils";

initialize();

const meta: Meta<typeof GlobalSearchButton> = {
  title: "Components/GlobalSearch",
  component: GlobalSearchButton,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
    msw: { handlers: [MOCK_SEARCH] },
  },
};

export default meta;

type Story = StoryObj<typeof GlobalSearchButton>;

export const Default: Story = {
  play: async ({ canvasElement }) => {
    const searchButton = await within(canvasElement).findByLabelText("Zoeken");
    userEvent.click(searchButton);

    const input = await within(canvasElement).findByRole("textbox");
    await userEvent.clear(input);
    await userEvent.type(input, "Aanvraag vergunning", { delay: 30 });
  },
};
