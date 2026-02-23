import type { Meta, StoryObj } from "@storybook/react";
import { HttpResponse, http } from "msw";
import { initialize, mswLoader } from "msw-storybook-addon";
import {
  reactRouterParameters,
  withRouter,
} from "storybook-addon-remix-react-router";
import { userEvent, within } from "storybook/test";

import { withCSRF } from "../../../.storybook/decorators.tsx";
import { Login } from "./login";
import { loginAction } from "./login.actions";

initialize();

const MOCK_CORRECT_LOGIN = http.post("/api/v1/accounts/login", () =>
  HttpResponse.json({
    isAuthenticated: true,
    user: {
      pk: 1,
      email: "johndoe@example.com",
      firstName: "John",
      lastName: "Doe",
      username: "johndoe",
    },
  }),
);

const MOCK_INCORRECT_LOGIN = http.post("/api/v1/accounts/login", () =>
  HttpResponse.json(
    {
      nonFieldErrors: ["Kan niet inloggen met de opgegeven gegevens.\n"],
    },
    { status: 400 },
  ),
);

const meta: Meta<typeof Login> = {
  title: "Routes/Login",
  component: Login,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: reactRouterParameters({
      routing: {
        action: loginAction,
      },
    }),
  },
};

export default meta;

type Story = StoryObj<typeof Login>;

export const CorrectLogin: Story = {
  parameters: {
    msw: {
      handlers: [MOCK_CORRECT_LOGIN],
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
      handlers: [MOCK_INCORRECT_LOGIN],
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
