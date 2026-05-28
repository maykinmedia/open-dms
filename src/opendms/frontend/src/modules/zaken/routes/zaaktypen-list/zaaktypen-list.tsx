import {
  Badge,
  BaseTemplate,
  Body,
  type Field,
  ListTemplate,
  Outline,
  P,
  type TypedField,
  Value,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { type JSX, useEffect, useState } from "react";
import {
  useLoaderData,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
import { apiClient, getPageFromSearchParams } from "~/lib";
import type { ZaakType } from "~/types";

import type { zaaktypenListLoader } from "./zaaktypen-list.loader";

type ZaaktypeListData = ZaakType & {
  href?: string;
  status?: JSX.Element;
  open_zaken?: JSX.Element;
};

/**
 * Renders a list component that displays a collection of "zaaktypen" (case types) with related metadata in a data grid format.
 * The component utilizes navigation, search parameters, and dynamic data loading to manage and render the list.
 *
 * @return {JSX.Element | boolean} A React functional component rendering the data grid structure populated with zaaktypen data.
 * Returns `false` if the required data is not available.
 */
export function ZaaktypenList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug } = useParams() as {
    serviceSlug: string | undefined;
  };

  const data = useLoaderData<typeof zaaktypenListLoader>();

  // No service selected.
  if (!serviceSlug) return <NoServiceSelectedMessage />;
  if (!data) return false;

  const objectList: ZaaktypeListData[] = data.results.map((zaaktype) => ({
    ...zaaktype,
    href: `zaaktypen/${zaaktype.uuid}`,
  }));

  // The fields to show in the datagrid.
  const fields: Array<Field<ZaaktypeListData> | TypedField<ZaaktypeListData>> =
    [
      "identificatie",
      "omschrijving",
      { name: "versiedatum", type: "date" },
      { name: "beginGeldigheid", type: "date" },
      { name: "eindeGeldigheid", type: "date" },
      {
        name: "status",
        type: "jsx",
        valueTransform: ZaaktypeStatusBadge,
      },
      {
        name: "open_zaken",
        type: "jsx",
        valueTransform: ZaaktypeZakenCount,
      },
    ];

  return (
    <ListTemplate<ZaaktypeListData>
      dataGridProps={{
        title: `${serviceSlug} / zaaktypen`,
        toolbarItems: [
          {
            type: "text",
            name: "omschrijving__icontains",
            placeholder: "Zoeken…",
            size: "s",
            onBlur: (e: unknown) => {
              const target = (e as React.FocusEvent<HTMLInputElement>).target;
              const name = target.name;
              const value = target.value;

              if (value) setSearchParams({ [name]: value });
              else setSearchParams({});
            },
          },
        ],
        objectList: objectList,
        fields: fields,
        paginatorProps: {
          count: data.count,
          page: getPageFromSearchParams(searchParams),
          pageSize: 100,
        },
        onPageChange: (page) =>
          setSearchParams({ ...searchParams, page: page.toString() }),
        onClick: (e, item) => {
          e.preventDefault();
          navigate(item.uuid);
        },
      }}
    />
  );
}

/**
 * Renders a message informing the user to select a service.
 *
 * @return {JSX.Element} A message component wrapped in a layout structure.
 */
function NoServiceSelectedMessage() {
  return (
    <BaseTemplate
      grid
      gridProps={{ valign: "middle" }}
      columnProps={{ justify: "center" }}
    >
      <Body>
        <P muted>Selecteer service.</P>
      </Body>
    </BaseTemplate>
  );
}

/**
 * Renders a Badge component indicating the status (Conecept/Definitief) of a Zaaktype.
 */
function ZaaktypeStatusBadge({ concept }: ZaakType): JSX.Element {
  return concept ? (
    <Badge variant="info">Concept</Badge>
  ) : (
    <Badge variant="success">Definitief</Badge>
  );
}

/**
 * Renders a Badge component indicating the status (Conecept/Definitief) of a Zaaktype.
 */
function ZaaktypeZakenCount({ uuid }: ZaakType): JSX.Element {
  const [loadingState, setLoadingState] = useState<boolean>(true);
  const [countState, setCountState] = useState<number | string>();
  const { serviceSlug } = useParams();
  invariant(serviceSlug, `serviceSlug not found!`);

  const fetchZakenCount = async (uuid: string, signal: AbortSignal) => {
    if (signal.aborted) return;

    try {
      setLoadingState(true);
      const { data } = await apiClient.GET(
        "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken",
        {
          params: {
            path: {
              serviceSlug,
              zaaktypenZaaktypeUuid: uuid,
            },
            query: {
              einddatum__isnull: true,
            },
          },
          signal: signal,
        },
      );
      setCountState(data?.count);
      setLoadingState(false);
    } catch (e) {
      if (signal.aborted) return;
      console.warn(e);
      setCountState(undefined);
    } finally {
      if (!signal.aborted) setLoadingState(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchZakenCount(uuid, controller.signal);
    return () => controller.abort("effect cleanup");
  }, [uuid]);

  return loadingState ? (
    <Outline.ArrowPathIcon spin aria-label="Bezig met laden" />
  ) : (
    <Value value={countState} decorate={true} />
  );
}
