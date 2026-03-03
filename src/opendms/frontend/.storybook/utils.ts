import type { RouteObject } from "react-router";
import {
  type ReactRouterAddonStoryParameters,
  reactRouterParameters,
} from "storybook-addon-remix-react-router";
import { routes } from "~/routes.ts";

/**
 * Generates sanitized parameters for React Router integration with Storybook.
 * Processes the routing configuration by removing unnecessary middlewares
 * from the provided routes and returns React Router-specific parameters.
 *
 * @return {ReactRouterAddonStoryParameters} The sanitized React Router parameters
 *                                           configured for Storybook.
 */
export function sanitizedReactRouterParameters(
  path = "/",
): ReactRouterAddonStoryParameters {
  return reactRouterParameters({
    location: { path },
    routing: stripMiddlewareFromRoutes(routes),
  });
}

/**
 * Removes the `middleware` property from each route object in the provided array.
 *
 * @param {Array} routes - The array of route objects where the first element is
 *                         the primary route and the rest are additional routes.
 *                         Each route object can optionally include a `middleware` property.
 * @return {Array} A new array of route objects with the `middleware` property removed,
 *                 maintaining the same structure as the input.
 */
export function stripMiddlewareFromRoutes([first, ...rest]: [
  RouteObject,
  ...RouteObject[],
]): [RouteObject, ...RouteObject[]] {
  const newFirst: RouteObject = { ...first };
  delete newFirst.middleware;

  const newRest: RouteObject[] = rest.map((route) => {
    const newRoute: RouteObject = { ...route };
    delete newRoute.middleware;
    return newRoute;
  });

  return [newFirst, ...newRest];
}
