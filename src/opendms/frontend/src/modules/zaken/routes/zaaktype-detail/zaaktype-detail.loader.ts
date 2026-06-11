import { invariant } from "@maykin-ui/client-common";
import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { StatusType, Zaak, ZaakType } from "~/types";

export type ZaakWithStatus = Zaak & { statustype: string | null };

export async function zaaktypeDetailLoader({
  params,
}: LoaderFunctionArgs): Promise<{
  zaaktype: ZaakType;
  statustypen: StatusType[];
  zaken: ZaakWithStatus[];
}> {
  if (!params.serviceSlug || !params.zaaktypeUuid) {
    throw new Response("Not Found", { status: 404 });
  }

  const { serviceSlug, zaaktypeUuid } = params;

  const [zaaktypeRes, statustypenRes, zakenRes] = await Promise.all([
    apiClient.GET("/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}", {
      params: { path: { serviceSlug, zaaktypeUuid } },
    }),
    apiClient.GET(
      "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/statustypen",
      {
        params: {
          path: { serviceSlug, zaaktypenZaaktypeUuid: zaaktypeUuid },
        },
      },
    ),
    apiClient.GET(
      "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken",
      {
        params: {
          path: { serviceSlug, zaaktypenZaaktypeUuid: zaaktypeUuid },
        },
      },
    ),
  ]);

  if (!zaaktypeRes.response.ok)
    throw new Error(zaaktypeRes.response.statusText);
  if (!statustypenRes.response.ok)
    throw new Error(statustypenRes.response.statusText);
  if (!zakenRes.response.ok) throw new Error(zakenRes.response.statusText);
  invariant(
    zaaktypeRes.data && statustypenRes.data && zakenRes.data,
    "Failed to load data!",
  );

  const rawZaken = zakenRes.data.results as Array<
    Zaak & { statustype?: string | null }
  >;

  return {
    zaaktype: zaaktypeRes.data,
    statustypen: [...statustypenRes.data.results].sort(
      (a, b) => a.volgnummer - b.volgnummer,
    ),
    zaken: rawZaken.map((z) => ({ ...z, statustype: z.statustype ?? null })),
  };
}
