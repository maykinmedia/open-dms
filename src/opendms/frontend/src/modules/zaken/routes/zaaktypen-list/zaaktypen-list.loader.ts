import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { ZaakType } from "~/types";

export async function zaaktypenListLoader({
  request,
  params,
}: LoaderFunctionArgs): Promise<{
  count: number;
  results: ZaakType[];
} | null> {
  if (!params.serviceSlug) return null;

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const { data, response } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen",
    {
      params: {
        path: { serviceSlug: params.serviceSlug },
        query: {
          page: parseInt(urlSearchParams.get("page") || "1"),
          omschrijving__icontains: urlSearchParams.get(
            "omschrijving__icontains",
          ),
        },
      },
    },
  );

  if (!response.ok) throw new Error(response.statusText);
  invariant(data, "Failed to load data!");
  return data;
}
