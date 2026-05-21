import { invariant } from "@maykin-ui/client-common";
import { useMatches } from "react-router";

/**
 * Retrieves the matched child route of the module's root route. This is determined
 * by finding the route with a `handle` property containing `moduleRoot: true`.
 *
 * The primary use case of this hook is to determine the path of the current module.
 *
 * Throws an error if no module root or its child route is found.
 *
 * @return {object} The route object corresponding to the matched child route under the module root.
 */
export function useModuleRouteMatch() {
  const matches = useMatches();
  const moduleRootIndex = matches.findIndex((match) => {
    const handle = match.handle as { moduleRoot?: boolean } | undefined;
    if (!handle) return false;
    if (handle.moduleRoot) return true;
  });

  invariant(
    moduleRootIndex > -1,
    "No module root found! Please set `handle: { moduleRoot: true }` on parent route of modules.",
  );

  const moduleIndex = moduleRootIndex + 1;
  const moduleRouteMatch = matches[moduleIndex];

  invariant(moduleRouteMatch, "Child route of moduleRoot not found!");
  return moduleRouteMatch;
}
