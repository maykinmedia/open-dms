import { Body, Breakout, Button, Outline } from "@maykin-ui/admin-ui";
import { useEffect, useMemo, useState } from "react";
import { NavLink, useParams } from "react-router";
import { apiClient } from "~/lib";
import type { ZaakType } from "~/types";

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:service_slug/:zaaktype_slug` upon selection
 */
export function YearSelect() {
  const [zaaktypeState, setZaaktypeState] = useState<ZaakType>();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid, zaakYear } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
    zaakYear: string | undefined;
  };
  const activeYear = zaakYear ? parseInt(zaakYear) : undefined;

  useEffect(() => {
    if (!serviceSlug || !zaaktypeUuid) return;
    apiClient
      // @ts-expect-error: api not yet rady
      .GET("/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}", {
        params: {
          path: {
            serviceSlug,
            zaaktypeUuid,
          },
        },
      })
      .then(({ data }) => setZaaktypeState(data));
  }, [serviceSlug, zaaktypeUuid]);

  /**
   * A memoized array of years based on the validity period of the `zaaktypeState`.
   * The array is generated starting from the year extracted from `beginGeldigheid`
   * and ends at the year extracted from `eindeGeldigheid` if it exists, or the
   * current year otherwise.
   *
   * The computation is dependent on the `zaaktypeState` object, and an empty
   * array is returned if `zaaktypeState` is not defined.
   *
   * @constant {number[]} years - The array of years representing the range of validity.
   */
  const years = useMemo(() => {
    if (!zaaktypeState) return [];

    const start = new Date(zaaktypeState.beginGeldigheid).getFullYear();
    const end = zaaktypeState.eindeGeldigheid
      ? new Date(zaaktypeState.eindeGeldigheid).getFullYear()
      : new Date().getFullYear();

    return Array.from({ length: end - start + 1 }, (_, i) => end - i);
  }, [zaaktypeState]);

  return (
    zaaktypeUuid &&
    zaaktypeState && (
      <Body allowScroll={true}>
        {years.map((year) => (
          <NavLink key={year} to={`/${serviceSlug}/${zaaktypeUuid}/${year}`}>
            <Breakout>
              <Button
                align="space-between"
                variant="transparent"
                active={year === activeYear}
              >
                {year}
                <Outline.ArrowRightIcon />
              </Button>
            </Breakout>
          </NavLink>
        ))}
      </Body>
    )
  );
}
