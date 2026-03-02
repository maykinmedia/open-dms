import { type LoadOptionsFn, type Option, Select } from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useNavigate, useParams } from "react-router";
import { apiClient } from "~/lib";

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:serviceSlug/:zaaktypeSlug` upon selection
 */
export function ZaaktypeSelect() {
  const navigate = useNavigate();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeSlug } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeSlug: string | undefined;
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
      // @ts-expect-error: api not yet rady
      `/api/v1/services/${serviceSlug}/zaaktypen`,
      {
        params: {
          query: {
            search,
          },
        },
      },
    );

    return (
      // @ts-expect-error: api not yet rady
      data?.results.map(({ label, slug }) => ({
        label,
        value: slug,
      })) || []
    );
  };

  /**
   * Routes to `:zaaktypeSlug`
   * @param value
   */
  const setSelectedZaaktype = (value: string) => {
    invariant(serviceSlug, "Can't select zaaktypeSlug without serviceSlug!");
    navigate(`/${serviceSlug}/${value}`);
  };

  return (
    serviceSlug && ( // https://github.com/maykinmedia/admin-ui/issues/301
      <Select
        disabled={!serviceSlug} // https://github.com/maykinmedia/admin-ui/issues/301
        labelNoOptions="Geen resultaten"
        options={getZaaktypeOptions}
        placeholder="Selecteer zaaktype"
        placeholderSearch="Zoeken"
        value={zaaktypeSlug}
        variant="secondary"
        onChange={({ target }) => setSelectedZaaktype(target.value)}
      />
    )
  );
}
