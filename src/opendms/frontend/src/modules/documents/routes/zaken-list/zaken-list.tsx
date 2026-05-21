import {
  A,
  BaseTemplate,
  Body,
  ListTemplate,
  P,
  type TypedField,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import type { JSX } from "react";
import {
  useLoaderData,
  useNavigate,
  useParams,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import { useModuleBasePath } from "~/hooks/usemodule";
import { getPageFromSearchParams } from "~/lib";
import type { Zaak } from "~/types";

import type { zaaktypeLoader } from "../../documents-module.loader";
import type { zakenListLoader } from "./zaken-list.loader";

export function ZakenList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const moduleBasePath = useModuleBasePath();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid, zaakYear } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
    zaakYear: string | undefined;
  };

  const rootData = useRouteLoaderData<typeof zaaktypeLoader>("documents-root");

  const data = useLoaderData<typeof zakenListLoader>();

  // No service, zaaktype and year selected.
  if (!data) {
    return <NoServiceZaaktypeAndYearSelectedMessage />;
  }
  invariant(rootData?.zaaktype, "Zaaktype not loaded!");

  // The fields to show in the datagrid.
  const fields: TypedField<
    Omit<Zaak, "identificatie"> & { identificatie: JSX.Element }
  >[] = [
    {
      name: "identificatie",
      type: "jsx",
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

  const objectList = data.results.map((zaak) => {
    const href = `${moduleBasePath}/${serviceSlug}/${zaaktypeUuid}/${zaakYear}/${zaak.uuid}`;
    return {
      ...zaak,
      identificatie: (
        <A
          href={href}
          onClick={(e) => {
            e.preventDefault();
            return navigate(href);
          }}
        >
          {zaak.identificatie}
        </A>
      ),
    };
  });

  return (
    <ListTemplate
      dataGridProps={{
        title: `${rootData.zaaktype.identificatie} / ${zaakYear}`,
        objectList: objectList,
        fields: fields,
        filterable: true,
        urlFields: [""],
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
