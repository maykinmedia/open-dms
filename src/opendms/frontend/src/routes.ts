import { createBrowserRouter } from "react-router";
import { Login, loginAction } from "~/routes/index.ts";

import { authRouterMiddleware } from "./middleware/auth.ts";
import { AuthenticatedLayout, Layout } from "./root.tsx";

/**
 * Built in "Data Mode" style using createBrowserRouter. https://reactrouter.com/start/modes#data
 * - _index is the top-level layout for public pages.
 * - To protect certain route(-groups) for authentication, we can make use of the middleware: (https://reactrouter.com/how-to/middleware)
 */
export const routes = createBrowserRouter([
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
        index: true,
        Component: () => "Authenticated",
      },
      // other protected routes here
    ],
  },
]);
