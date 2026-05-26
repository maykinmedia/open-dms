import { invariant } from "@maykin-ui/client-common";
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

  const { data: zaak } = await apiClient.GET(
    "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken/{zaakUuid}",
    {
      params: {
        path: {
          serviceSlug: params.serviceSlug,
          zaaktypenZaaktypeUuid: params.zaaktypeUuid,
          zaakUuid: params.zaakId,
        },
      },
    },
  );

  const { data: documentData } = await fetchDocuments(
    params.serviceSlug,
    params.zaaktypeUuid,
    params.zaakId,
    page,
  );

  invariant(zaak);
  invariant(documentData);
  return { ...documentData, zaak };
}

export async function unlinkedDocumentsListLoader({
  params,
  request,
}: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const urlSearchParams = new URLSearchParams(url.search);
  const page = Number(urlSearchParams.get("page")) || undefined;

  const { data: documentData } = await fetchDocuments(
    params.serviceSlug,
    undefined,
    undefined,
    page,
  );

  return documentData;
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
  zaaktypeUuid?: string,
  zaakId?: string,
  page?: number | string,
  signal?: AbortSignal,
) {
  if (!zaaktypeUuid && !zaakId) {
    return await apiClient.GET(
      "/api/v1/services/{serviceSlug}/unlinked-documents",
      {
        params: {
          path: {
            serviceSlug: serviceSlug,
          },
          query: {
            page: page ? parseInt(page as string) : undefined,
          },
        },
        signal,
      },
    );
  }

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
        },
      },
      signal,
    },
  );
}
