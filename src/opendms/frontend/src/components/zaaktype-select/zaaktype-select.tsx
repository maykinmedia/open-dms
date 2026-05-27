import { type LoadOptionsFn, type Option, Select } from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useMatch, useNavigate, useParams } from "react-router";
import { apiClient } from "~/lib";

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:serviceSlug/:zaaktypeUuid` upon selection
 */
export function ZaaktypeSelect() {
  const navigate = useNavigate();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
  };

  const ONBEKEND_VALUE = "onbekend";

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
      `/services/{serviceSlug}/zaaktypen`,
      {
        params: {
          path: { serviceSlug },
          query: {
            search,
          },
        },
      },
    );

    const zaaktypeOptions: Option[] =
      data?.results.map(({ identificatie, uuid }) => ({
        label: identificatie,
        value: uuid,
      })) || [];

    return [...zaaktypeOptions, { label: "Onbekend", value: ONBEKEND_VALUE }];
  };

  /**
   * Routes to `:zaaktypeUuid` or `onbekend`
   * @param value
   */
  const setSelectedZaaktype = (value: string) => {
    invariant(serviceSlug, "Can't select zaaktypeUuid without serviceSlug!");
    if (value === ONBEKEND_VALUE) {
      navigate(`/${serviceSlug}/onbekend`);
    } else {
      navigate(`/${serviceSlug}/${value}`);
    }
  };

  const onbekendIndexMatch = useMatch("/:serviceSlug/onbekend");
  const onbekendUuidMatch = useMatch("/:serviceSlug/onbekend/:iotUuid");
  const currentValue =
    onbekendIndexMatch || onbekendUuidMatch ? ONBEKEND_VALUE : zaaktypeUuid;

  return (
    serviceSlug && ( // TODO: https://github.com/maykinmedia/admin-ui/issues/301
      <Select
        disabled={!serviceSlug} // TODO: https://github.com/maykinmedia/admin-ui/issues/301
        labelNoOptions="Geen resultaten"
        options={getZaaktypeOptions}
        placeholder="Selecteer zaaktype"
        placeholderSearch="Zoeken"
        value={currentValue}
        variant="secondary"
        onChange={({ target }) => setSelectedZaaktype(target.value)}
      />
    )
  );
}
