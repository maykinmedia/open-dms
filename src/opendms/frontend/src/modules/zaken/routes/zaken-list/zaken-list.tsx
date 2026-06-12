import {
  Badge,
  type BadgeProps,
  BaseTemplate,
  Body,
  type Field,
  ListTemplate,
  Outline,
  P,
  type TypedField,
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
import { getUUIDFromUrl } from "~/lib/url.ts";
import type { StatusType, Zaak, ZaakType } from "~/types";

import type { zakenListLoader } from "./zaken-list.loader";

// Loader
type LoaderData = Awaited<ReturnType<typeof zakenListLoader>>;
type ExpandedZaak = Exclude<LoaderData, null>["results"][number];
type ZaakListData = ExpandedZaak & { status: string };

/**
 * Renders a list component that displays a collection of "zaken" (case types) with related metadata in a data grid format.
 * The component utilizes navigation, search parameters, and dynamic data loading to manage and render the list.
 *
 * @return {JSX.Element | boolean} A React functional component rendering the data grid structure populated with zaken data.
 * Returns `false` if the required data is not available.
 */
export function ZakenList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug } = useParams() as {
    serviceSlug: string | undefined;
  };

  const data = useLoaderData<typeof zakenListLoader>();

  // No service selected.
  if (!serviceSlug) return <NoServiceSelectedMessage />;
  if (!data) return false;

  const objectList: ZaakListData[] = data.results.map((zaak) => ({
    ...zaak,
    href: `zaken/${zaak.uuid}`,
    status: zaak._expand.status.statustype,
  }));

  // The fields to show in the datagrid.
  const fields: Array<Field<ZaakListData> | TypedField<ZaakListData>> = [
    "identificatie",
    "omschrijving",
    {
      name: "zaaktype",
      type: "text",
      valueTransform: ZaakTypeBadge,
    },
    "startdatum",
    {
      name: "status",
      type: "text",
      valueTransform: StatusBadge,
    },
  ];

  return (
    <ListTemplate<ZaakListData>
      dataGridProps={{
        title: `${serviceSlug} / zaken`,
        toolbarItems: [
          {
            type: "text",
            name: "identificatie__icontains",
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
 * Renders a Badge component indicating the ZaakType of a Zaak.
 */
function ZaakTypeBadge({ zaaktype: zaaktypeUrl }: Zaak): JSX.Element {
  const [loadingState, setLoadingState] = useState<boolean>(true);
  const [zaakTypeState, setZaakTypeState] = useState<ZaakType>();
  const navigate = useNavigate();
  const { serviceSlug } = useParams();
  invariant(serviceSlug, `serviceSlug not found!`);
  const zaaktypeUuid = getUUIDFromUrl(zaaktypeUrl);

  const fetchZaakType = async (zaaktypeUuid: string, signal: AbortSignal) => {
    if (signal.aborted) return;

    try {
      setLoadingState(true);
      const { data } = await apiClient.GET(
        "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypeUuid}",
        {
          params: {
            path: {
              serviceSlug,
              zaaktypeUuid,
            },
          },
          signal: signal,
        },
      );
      setZaakTypeState(data);
      setLoadingState(false);
    } catch (e) {
      if (signal.aborted) return;
      console.warn(e);
      setZaakTypeState(undefined);
    } finally {
      if (!signal.aborted) setLoadingState(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchZaakType(zaaktypeUuid, controller.signal);
    return () => controller.abort("effect cleanup");
  }, [zaaktypeUrl]);

  return loadingState ? (
    <Outline.ArrowPathIcon spin aria-label="Bezig met laden" />
  ) : (
    <Badge onClick={() => navigate(`../zaaktypen/${zaaktypeUuid}`)}>
      {zaakTypeState?.omschrijving}
    </Badge>
  );
}

/**
 * Renders a Badge component indicating the ZaakType of a Zaak.
 */
function StatusBadge(expandedZaak: ExpandedZaak): JSX.Element {
  const [loadingState, setLoadingState] = useState<boolean>(true);
  const [statusTypeState, setStatusTypeState] = useState<StatusType>();
  const { serviceSlug } = useParams();
  invariant(serviceSlug, `serviceSlug not found!`);
  const statustypeUuid = getUUIDFromUrl(expandedZaak._expand.status.statustype);

  const fetchStatusType = async (
    statustypeUuid: string,
    signal: AbortSignal,
  ) => {
    if (signal.aborted) return;

    try {
      setLoadingState(true);
      const { data } = await apiClient.GET(
        "/api/v1/services/{serviceSlug}/statustypen/{statustypeUuid}",
        {
          params: {
            path: {
              serviceSlug,
              statustypeUuid,
            },
          },
          signal: signal,
        },
      );
      setStatusTypeState(data);
      setLoadingState(false);
    } catch (e) {
      if (signal.aborted) return;
      console.warn(e);
      setStatusTypeState(undefined);
    } finally {
      if (!signal.aborted) setLoadingState(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchStatusType(statustypeUuid, controller.signal);
    return () => controller.abort("effect cleanup");
  }, [statustypeUuid]);

  if (loadingState) {
    return <Outline.ArrowPathIcon spin aria-label="Bezig met laden" />;
  } else {
    invariant(statusTypeState, "statusType not loaded!");
    type Variant = BadgeProps["variant"];
    const variants: Variant[] = ["info", "info", "warning", "danger"];
    const index = Math.min(
      Math.max(statusTypeState.volgnummer - 1, 0),
      variants.length - 1,
    );
    const variant = variants[index];

    return <Badge variant={variant}>{statusTypeState?.omschrijving}</Badge>;
  }
}
