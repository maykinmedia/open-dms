import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Document } from "~/types";

export async function documentsListLoader({
  params,
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

  const { data } = await apiClient.GET(
    // @ts-expect-error - API not ready
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}/zaken/zaakYear/{zaakYear}/zaakId/{zaakId}",
    {
      params: {
        path: params,
      },
    },
  );

  // @ts-expect-error - API not ready
  return data;
}
