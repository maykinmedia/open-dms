import type { RouteObject } from "react-router";

import { Login, loginAction, loginLoader } from "./routes/index";

export const routes: RouteObject[] = [
  {
    path: "login",
    Component: Login,
    loader: loginLoader,
    action: loginAction,
  },
];
