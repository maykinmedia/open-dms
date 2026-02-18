import { createBrowserRouter } from "react-router";

import { authMiddleware } from "./middleware/auth.ts";
import { Layout } from "./root.tsx";
import { Index } from "./routes/_index.tsx";

/**
 * Built in "Data Mode" style using createBrowserRouter. https://reactrouter.com/start/modes#data
 * - _index is the top-level layout for public pages.
 * - To protect certain route(-groups) for authentication, we can make use of the middleware: (https://reactrouter.com/how-to/middleware)
 */
export const routes = createBrowserRouter([
  {
    Component: Layout,
    children: [
      { index: true, Component: Index },
      {
        middleware: [authMiddleware],
        children: [
          {
            path: "auth",
          },
        ],
      },
    ],
  },
  //     // TODO: Implement 404:
  //     // { path: "*", element: <NotFound /> },
  //   ],
  // },
]);
