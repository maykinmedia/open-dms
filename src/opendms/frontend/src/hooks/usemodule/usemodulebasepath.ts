import { useModuleRouteMatch } from "~/hooks/usemodule/usemoduleroutematch.ts";

/**
 * Retrieves and returns the base path of the current module.
 *
 * This method utilizes the `useModuleRouteMatch` hook to extract the `pathname`
 * of the matched route, which represents the base path of the module.
 *
 * @return {string} The base path of the current module.
 */
export function useModuleBasePath() {
  const moduleRouteMatch = useModuleRouteMatch();
  return moduleRouteMatch.pathname;
}
