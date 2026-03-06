import { delay } from "@maykin-ui/client-common";
import { type RouteObject } from "react-router";
import {
  type ReactRouterAddonStoryParameters,
  reactRouterParameters,
} from "storybook-addon-remix-react-router";
import { expect, waitFor, within } from "storybook/test";
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

/**
 * Waits for the specified canvas element to reach an "idle" state. This is typically used
 * to pause execution until the element is ready for further operations after any pending
 * activity or rendering processes.
 *
 * @param {HTMLElement} canvasElement - The canvas element to monitor for the "idle" state.
 * @return {Promise<void>} A promise that resolves when the canvas element reaches the "idle" state.
 */
export async function waitForIdle(canvasElement: HTMLElement): Promise<void> {
  return waitForState(canvasElement, "idle");
}

/**
 * Waits until the specified canvas element enters the `"loading"` navigation state.
 *
 * This resolves once a loading indicator labeled `"Bezig met laden"` becomes
 * present within the provided canvas element.
 *
 * @param canvasElement - The canvas element to monitor.
 * @returns A promise that resolves once the canvas enters the `"loading"` state.
 */
export function waitForLoading(canvasElement: HTMLElement): Promise<void> {
  return waitForState(canvasElement, "loading");
}

/**
 * Waits until the specified canvas element enters the `"submitting"` navigation state.
 *
 * This resolves once a loading indicator labeled `"Bezig met laden"` becomes
 * present within the provided canvas element.
 *
 * @param canvasElement - The canvas element to monitor.
 * @returns A promise that resolves once the canvas enters the `"submitting"` state.
 */
export function waitForSubmitting(canvasElement: HTMLElement): Promise<void> {
  return waitForState(canvasElement, "submitting");
}

/**
 * Waits until the given canvas element reflects the specified navigation state.
 *
 * The state is inferred by checking for the presence of an element labeled
 * `"Bezig met laden"` within the canvas element.
 *
 * - `"idle"` → the loading indicator must **not** be present
 * - `"loading"` or `"submitting"` → the loading indicator must **be** present
 *
 * Internally this uses `waitFor` to repeatedly evaluate the DOM until the
 * expected condition is satisfied or the timeout is reached.
 *
 * @param canvasElement - The canvas element whose navigation state should be observed.
 * @param state - The navigation state to wait for (`"idle"`, `"loading"`, or `"submitting"`).
 * @returns A promise that resolves once the expected state is observed.
 */
export async function waitForState(
  canvasElement: HTMLElement,
  state: "idle" | "loading" | "submitting",
): Promise<void> {
  await waitFor(() => {
    const spinner = within(canvasElement).queryByLabelText("Bezig met laden");

    switch (state) {
      case "idle":
        expect(spinner).toBeNull();
        break;

      case "loading":
      case "submitting":
        expect(spinner).toBeInTheDocument();
        break;

      default: {
        const exhaustive: never = state;
        throw new Error(`Unhandled navigation state: ${exhaustive}`);
      }
    }
  });

  // Allow UI updates to flush after the navigation state settles.
  await delay();
}
