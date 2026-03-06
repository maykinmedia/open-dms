import { formatDate } from "@storybook/addon-docs/blocks";
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
  if (!params.serviceSlug || !params.zaaktypeUuid || !params.zaakYear)
    return null;

  const startdatum = new Date(params.zaakYear);
  if (isNaN(startdatum.getFullYear())) return null; // Not a valid date, bail early.

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const { data } = await apiClient.GET(
    // @ts-expect-error - API not ready
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}/zaken",
    {
      params: {
        path: params,
        query: {
          startdatum__gte: formatDate(startdatum),
          identificatie__icontains: urlSearchParams.get(
            "identificatie__icontains",
          ),
          omschrijving: urlSearchParams.get("omschrijving"),
          page: urlSearchParams.get("page"),
        },
      },
    },
  );

  // @ts-expect-error - API not ready
  return data;
}
