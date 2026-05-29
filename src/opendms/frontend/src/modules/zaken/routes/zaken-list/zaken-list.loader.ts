import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Zaak, ZaakType } from "~/types";

export async function zakenListLoader({
  request,
  params,
}: LoaderFunctionArgs): Promise<{
  zaaktype: ZaakType;
  count: number;
  results: Zaak[];
} | null> {
  if (!params.serviceSlug || !params.zaaktypeUuid) return null;

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const [zaaktypeResponse, zakenResponse] = await Promise.all([
    apiClient.GET("/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}", {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypeUuid: params.zaaktypeUuid,
        },
      },
    }),
    apiClient.GET(
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
    ),
  ]);

  if (!zaaktypeResponse.response.ok)
    throw new Error(zaaktypeResponse.response.statusText);
  if (!zakenResponse.response.ok)
    throw new Error(zakenResponse.response.statusText);

  invariant(zaaktypeResponse.data, "Failed to load zaaktype!");
  invariant(zakenResponse.data, "Failed to load zaken!");

  return {
    zaaktype: zaaktypeResponse.data,
    ...zakenResponse.data,
  };
}
