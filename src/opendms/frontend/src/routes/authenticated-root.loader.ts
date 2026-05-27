import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { ZaakType } from "~/types";

/**
 * Loads and returns the authenticated root resource for the specified service and zaaktype.
 * Performs an API call to fetch the requested resource based on the given parameters.
 *
 * @param {LoaderFunctionArgs} args - The loader function arguments containing parameters.
 * @param {object} args.params - The parameters passed to the loader function.
 * @param {string} args.params.serviceSlug - The unique identifier for the service.
 * @param {string} args.params.zaaktypeUuid - The UUID of the zaaktype.
 * @return {Promise<{ zaaktype: object | null }>} A promise that resolves to an object containing the zaaktype data,
 * or null if the required parameters are missing or the resource is not found.
 */
export async function authenticatedRootLoader({
  params,
}: LoaderFunctionArgs): Promise<{ zaaktype: ZaakType | undefined }> {
  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid } = params;
  if (!serviceSlug || !zaaktypeUuid) return { zaaktype: undefined };
  const { data: zaaktype } = await apiClient.GET(
    "/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}",
    {
      params: {
        path: {
          serviceSlug,
          zaaktypeUuid,
        },
      },
    },
  );
  return { zaaktype };
}
