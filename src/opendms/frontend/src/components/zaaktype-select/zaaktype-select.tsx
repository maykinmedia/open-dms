import { type LoadOptionsFn, type Option, Select } from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useNavigate, useParams } from "react-router";
import { apiClient } from "~/lib";

export type ZaaktypeSelectProps = {
  basepath?: string;
};

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:serviceSlug/:zaaktypeUuid` upon selection
 */
export function ZaaktypeSelect({ basepath = "/" }: ZaaktypeSelectProps) {
  const navigate = useNavigate();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
  };

  /**
   * Fetches the service options from the backend (client-side)
   * Accepts string as the first parameter according to `@maykin-ui / LoadOptionsFn` and returns a Promise of results
   * @param search
   */
  const getZaaktypeOptions: LoadOptionsFn = async (
    search,
  ): Promise<Option[]> => {
    if (!serviceSlug) return [];

    const { data } = await apiClient.GET(
      `/api/v1/services/{serviceSlug}/zaaktypen`,
      {
        params: {
          path: { serviceSlug },
          query: {
            search,
          },
        },
      },
    );

    return (
      data?.results.map(({ identificatie, uuid }) => ({
        label: identificatie,
        value: uuid,
      })) || []
    );
  };

  /**
   * Routes to `:zaaktypeUuid`
   * @param value
   */
  const setSelectedZaaktype = (value: string) => {
    invariant(serviceSlug, "Can't select zaaktypeUuid without serviceSlug!");
    navigate(`${basepath}/${serviceSlug}/${value}`);
  };

  return (
    serviceSlug && ( // TODO: https://github.com/maykinmedia/admin-ui/issues/301
      <Select
        disabled={!serviceSlug} // TODO: https://github.com/maykinmedia/admin-ui/issues/301
        labelNoOptions="Geen resultaten"
        options={getZaaktypeOptions}
        placeholder="Selecteer zaaktype"
        placeholderSearch="Zoeken"
        value={zaaktypeUuid}
        variant="secondary"
        onChange={({ target }) => setSelectedZaaktype(target.value)}
      />
    )
  );
}
