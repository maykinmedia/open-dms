import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { ZaakType } from "~/types";

/**
 * Loads the zaaktype for the currently selected service and zaaktype URL params
 * Returns undefined for the zaaktype when params are missing or the resource is not found
 */
export async function zaaktypeLoader({
  params,
}: LoaderFunctionArgs): Promise<{ zaaktype: ZaakType | undefined }> {
  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid } = params;
  if (!serviceSlug || !zaaktypeUuid) return { zaaktype: undefined };
  const { data: zaaktype } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}",
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
