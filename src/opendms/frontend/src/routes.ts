import { type RouteObject, createBrowserRouter, redirect } from "react-router";
import { authenticatedRootLoader } from "~/authenticated-root.loader.ts";
import { authRouterMiddleware, routes as authRoutes } from "~/modules/auth";

import { createModuleRoutes as createDocumentRoutes } from "./modules/documents";
import { createModuleRoutes as createZakenRoutes } from "./modules/zaken";
import { AuthenticatedLayout, Layout } from "./root.tsx";

export const routes: [RouteObject, ...RouteObject[]] = [
  {
    Component: Layout, // Public layout
    handle: { moduleRoot: true }, // Indicate module root, necessary for modules (apps) to work.
    children: authRoutes,
  },
  {
    id: "authenticated-root",
    Component: AuthenticatedLayout,
    middleware: [authRouterMiddleware],
    loader: authenticatedRootLoader,
    shouldRevalidate: () => true,
    handle: { moduleRoot: true }, // Indicate module root, necessary for modules (apps) to work.
    children: [
      ...createZakenRoutes("zaken"),
      ...createDocumentRoutes("documenten"),
      {
        index: true,
        loader: () => redirect("zaken"),
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
