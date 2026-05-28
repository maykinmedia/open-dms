import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Zaak } from "~/types";

export async function zakenListLoader({
  request,
  params,
}: LoaderFunctionArgs): Promise<{
  count: number;
  results: Zaak[];
} | null> {
  if (!params.serviceSlug || !params.zaaktypeUuid) return null;

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const { data, response } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypenZaaktypeUuid: params.zaaktypeUuid,
        },
        query: {
          page: parseInt(urlSearchParams.get("page") || "1"),
          identificatie__icontains:
            urlSearchParams.get("identificatie__icontains") ?? undefined,
          omschrijving: urlSearchParams.get("omschrijving") ?? undefined,
        },
      },
    },
  );

  if (!response.ok) throw new Error(response.statusText);
  invariant(data, "Failed to load data!");
  return data;
}
