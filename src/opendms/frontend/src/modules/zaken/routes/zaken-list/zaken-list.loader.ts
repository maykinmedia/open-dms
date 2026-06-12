import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import * as z from "zod";
import { apiClient } from "~/lib";

export async function zakenListLoader({ request, params }: LoaderFunctionArgs) {
  if (!params.serviceSlug) return null;

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const { data, response } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaken",
    {
      params: {
        path: { serviceSlug: params.serviceSlug },
        query: {
          page: parseInt(urlSearchParams.get("page") || "1"),
          identificatie__icontains:
            urlSearchParams.get("identificatie__icontains") || undefined,
          einddatum__isnull: true,
          ordering: "-startdatum",
          expand: "status",
        },
      },
    },
  );

  if (!response.ok) throw new Error(response.statusText);
  invariant(data, "Failed to load data!");

  // Expand is typed Record<string, never> as the schema is dynamic.
  // We use zod to parse the actual value and provide the proper result schema.
  const results = data.results.map((zaak) => {
    const StatusExpand = z.object({
      status: z.object({
        statustype: z.url(),
      }),
    });
    const _expand = z.parse(StatusExpand, zaak._expand);
    return { ...zaak, _expand };
  });

  return { ...data, results };
}
