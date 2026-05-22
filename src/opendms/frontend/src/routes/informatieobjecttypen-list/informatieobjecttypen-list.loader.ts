import type { LoaderFunctionArgs } from "react-router";
import { apiClient } from "~/lib";
import type { InformatieObjectType } from "~/types";

export async function informatieobjecttypenListLoader({
  params,
}: LoaderFunctionArgs): Promise<{
  count: number;
  results: InformatieObjectType[];
} | null> {
  if (!params.serviceSlug) return null;

  const { data } = await apiClient.GET(
    // @ts-expect-error - API not ready
    "/api/v1/services/{serviceSlug}/informatieobjecttypen",
    {
      params: {
        path: { serviceSlug: params.serviceSlug },
      },
    },
  );

  return (data as unknown as { count: number; results: InformatieObjectType[] }) ?? null;
}
