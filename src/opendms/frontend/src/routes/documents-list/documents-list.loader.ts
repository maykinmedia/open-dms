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
  const page = Number(urlSearchParams.get("page")) || undefined;

  const { data } = await fetchDocuments(
    params.serviceSlug,
    params.zaaktypeUuid,
    params.zaakId,
    page,
  );

  return data;
}

/**
 * Fetches a paginated list of documents for a given service, zaaktype, and zaak.
 *
 * @param {string} serviceSlug - The slug identifying the service.
 * @param {string} zaaktypeUuid - The UUID of the zaaktype.
 * @param {string} zaakId - The ID of the zaak.
 * @param {number|string} [page] - The page number for pagination. Can be a number or a string that can be parsed into a number.
 * @param {AbortSignal} [signal] - An optional AbortSignal to cancel the request.
 * @return {Promise} The response containing the documents.
 */
export async function fetchDocuments(
  serviceSlug: string,
  zaaktypeUuid: string,
  zaakId: string,
  page?: number | string,
  signal?: AbortSignal,
) {
  return await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken/{zakenZaakUuid}/documents",
    {
      params: {
        path: {
          serviceSlug: serviceSlug,
          zaaktypenZaaktypeUuid: zaaktypeUuid,
          zakenZaakUuid: zaakId,
        },
        query: {
          page: page ? parseInt(page as string) : undefined,
          pageSize: 20,
        },
      },
      signal,
    },
  );
}
