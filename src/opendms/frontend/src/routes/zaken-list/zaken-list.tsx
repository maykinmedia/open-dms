import {
  BaseTemplate,
  Body,
  ListTemplate,
  P,
  type TypedField,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import {
  useLoaderData,
  useParams,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import { getPageFromSearchParams } from "~/lib";
import { authenticatedRootLoader } from "~/routes/authenticated-root.loader.ts";
import type { Zaak } from "~/types";

import type { zakenListLoader } from "./zaken-list.loader";

export function ZakenList() {
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { zaakYear } = useParams() as {
    zaakYear: string | undefined;
  };

  const rootData =
    useRouteLoaderData<typeof authenticatedRootLoader>("authenticated-root");
  invariant(rootData?.zaaktype, "Zaaktype not loaded!");

  const data = useLoaderData<typeof zakenListLoader>();

  // No service, zaaktype and year selected.
  if (!data) {
    return <NoServiceZaaktypeAndYearSelectedMessage />;
  }

  // The fields to show in the datagrid.
  const fields: TypedField<Zaak>[] = [
    {
      name: "identificatie",
      type: "string",
      filterLookup: "identificatie__icontains",
      filterValue: searchParams.get("identificatie__icontains") ?? "",
    },
    {
      name: "omschrijving",
      type: "string",
      filterLookup: "omschrijving",
      filterValue: searchParams.get("omschrijving") ?? "",
    },
  ];

  return (
    <ListTemplate
      dataGridProps={{
        title: `${rootData.zaaktype.identificatie} / ${zaakYear}`,
        objectList: data.results,
        fields: fields,
        filterable: true,
        paginatorProps: {
          count: data.count,
          page: getPageFromSearchParams(searchParams),
          pageSize: 100,
        },
        onPageChange: (page) => setSearchParams({ page: page.toString() }),
        onFilter: (data: Record<string, string>) => {
          searchParams.delete("page");
          setSearchParams({
            ...Object.fromEntries(searchParams),
            ...data,
          });
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
