import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";

export async function documentsListLoader({
  params,
  request,
}: LoaderFunctionArgs) {
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
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken/{zakenZaakUuid}/documents",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypenZaaktypeUuid: params.zaaktypeUuid,
          zakenZaakUuid: params.zaakId,
        },
        query: {
          page: Number(urlSearchParams.get("page")) || undefined,
          pageSize: 20,
        },
      },
    },
  );

  return data;
}
