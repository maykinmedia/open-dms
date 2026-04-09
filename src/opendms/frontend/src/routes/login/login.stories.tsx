import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";

import { withCSRF } from "../../../.storybook/decorators.tsx";
import {
  MOCK_CORRECT_LOGIN,
  MOCK_INCORRECT_LOGIN,
  MOCK_WHOAMI,
} from "../../../.storybook/mocks.ts";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils.ts";
import { Login } from "./login";

initialize();

const meta: Meta<typeof Login> = {
  title: "Routes/Login",
  component: Login,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters("/login"),
  },
};

export default meta;

type Story = StoryObj<typeof Login>;

export const CorrectLogin: Story = {
  parameters: {
    msw: {
      handlers: [MOCK_WHOAMI, MOCK_CORRECT_LOGIN],
    },
  },
  play: async ({ canvasElement }) => {
    const usernameInput =
      await within(canvasElement).findByLabelText("Gebruikersnaam");
    const passwordInput =
      await within(canvasElement).findByLabelText("Wachtwoord");
    const submitButton = await within(canvasElement).findByRole("button");

    await userEvent.type(usernameInput, "johndoe");
    await userEvent.type(passwordInput, "s3cret");
    await userEvent.click(submitButton);
  },
};

export const IncorrectLogin: Story = {
  parameters: {
    msw: {
      handlers: [MOCK_WHOAMI, MOCK_INCORRECT_LOGIN],
    },
  },
  play: async ({ canvasElement }) => {
    const usernameInput =
      await within(canvasElement).findByLabelText("Gebruikersnaam");
    const passwordInput =
      await within(canvasElement).findByLabelText("Wachtwoord");
    const submitButton = await within(canvasElement).findByRole("button");

    await userEvent.type(usernameInput, "johndoe");
    await userEvent.type(passwordInput, "s3cret");
    await userEvent.click(submitButton);
  },
};
