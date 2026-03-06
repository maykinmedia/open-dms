import { Body, Breakout, Button, Outline } from "@maykin-ui/admin-ui";
import { useMemo } from "react";
import { NavLink, useLoaderData, useParams } from "react-router";

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:service_slug/:zaaktype_slug` upon selection
 */
export function YearSelect() {
  const { zaaktype } = useLoaderData();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid, zaakYear } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
    zaakYear: string | undefined;
  };
  const activeYear = zaakYear ? parseInt(zaakYear) : undefined;

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
    if (!zaaktype) return [];

    const start = new Date(zaaktype.beginGeldigheid).getFullYear();
    const end = zaaktype.eindeGeldigheid
      ? new Date(zaaktype.eindeGeldigheid).getFullYear()
      : new Date().getFullYear();

    return Array.from({ length: end - start + 1 }, (_, i) => end - i);
  }, [zaaktype]);

  return (
    zaaktypeUuid &&
    zaaktype && (
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
