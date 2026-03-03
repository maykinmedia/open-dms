import { type RouteObject, createBrowserRouter } from "react-router";
import {
  Login,
  ZakenList,
  loginAction,
  zakenListLoader,
} from "~/routes/index.ts";

import { authRouterMiddleware } from "./middleware/auth.ts";
import { AuthenticatedLayout, Layout } from "./root.tsx";

export const routes: [RouteObject, ...RouteObject[]] = [
  {
    Component: Layout, // Public layout
    children: [
      {
        path: "login",
        Component: Login,
        action: loginAction,
      },
    ],
  },
  {
    Component: AuthenticatedLayout,
    middleware: [authRouterMiddleware],
    children: [
      {
        path: ":serviceSlug?/:zaaktypeUuid?/:zaakYear?",
        children: [
          {
            index: true,
            Component: ZakenList,
            loader: zakenListLoader,
          },
        ],
      },
    ],
  },
];
/**
 * Built in "Data Mode" style using createBrowserRouter. https://reactrouter.com/start/modes#data
 * - _index is the top-level layout for public pages.
 * - To protect certain route(-groups) for authentication, we can make use of the middleware: (https://reactrouter.com/how-to/middleware)
 */
export const router = createBrowserRouter(routes);
