import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Document } from "~/types";

export async function documentsListLoader({
  params,
  request,
}: LoaderFunctionArgs): Promise<{
  count: number;
  results: Document[];
} | null> {
  if (
    !params.serviceSlug ||
    !params.zaaktypeUuid ||
    !params.zaakYear ||
    !params.zaakId
  )
    return null;

  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);

  const { data } = await apiClient.GET(
    // @ts-expect-error - API not ready
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}/zaken/{zaakId}/documents",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypeUuid: params.zaaktypeUuid,
          zaakId: params.zaakId,
        },
        query: {
          page: urlSearchParams.get("page"),
        },
      },
    },
  );

  // @ts-expect-error - API not ready
  return data;
}
