import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { Document } from "~/types";

export async function onbekendDocumentsListLoader({
  params,
  request,
}: LoaderFunctionArgs) {
  if (!params.serviceSlug || !params.iotUuid) return null;

  const url = new URL(request.url);
  const page = Number(url.searchParams.get("page")) || undefined;

  const { data } = await apiClient.GET(
    "/services/{serviceSlug}/informatieobjecttypen/{informatieobjecttypenIotUuid}/documents",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          informatieobjecttypenIotUuid: params.iotUuid,
        },
        query: {
          page: page,
          pageSize: 20,
        },
      },
    },
  );

  return (data as unknown as { count: number; results: Document[] }) ?? null;
}
