import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Zaak } from "~/types";

export async function zaakDetailLoader({
  params,
}: LoaderFunctionArgs): Promise<Zaak> {
  invariant(params.serviceSlug, "serviceSlug is required");
  invariant(params.zaaktypeUuid, "zaaktypeUuid is required");
  invariant(params.zaakUuid, "zaakUuid is required");

  const { data, response } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken/{zaakUuid}",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypenZaaktypeUuid: params.zaaktypeUuid,
          zaakUuid: params.zaakUuid,
        },
      },
    },
  );

  if (!response.ok) throw new Error(response.statusText);
  invariant(data, "Failed to load zaak!");
  return data;
}
