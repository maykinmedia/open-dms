import { BaseTemplate, Body, ListTemplate, P } from "@maykin-ui/admin-ui";
import { useLoaderData, useSearchParams } from "react-router";
import { getPageFromSearchParams } from "~/lib";

import type { zakenListLoader } from "./zaken-list.loader";

export function ZakenList() {
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof zakenListLoader>();

  // No service, zaaktype and year selected.
  if (!data) {
    return <NoServiceZaaktypeAndYearSelectedMessage />;
  }

  return (
    <ListTemplate
      dataGridProps={{
        objectList: data.results,
        fields: ["identificatie", "omschrijving"],
        paginatorProps: {
          count: data.count,
          page: getPageFromSearchParams(searchParams),
          pageSize: 100,
          onPageChange: (page) => setSearchParams({ page: page.toString() }),
        },
      }}
    />
  );
}

/**
 * Renders a message informing the user to select a service, zaaktype, and year to view an overview of cases.
 *
 * @return {JSX.Element} A message component wrapped in a layout structure.
 */
function NoServiceZaaktypeAndYearSelectedMessage() {
  return (
    <BaseTemplate
      grid
      gridProps={{ valign: "middle" }}
      columnProps={{ justify: "center" }}
    >
      <Body>
        <P muted>
          Selecteer service, zaaktype en jaar voor een overzicht van zaken.
        </P>
      </Body>
    </BaseTemplate>
  );
}
