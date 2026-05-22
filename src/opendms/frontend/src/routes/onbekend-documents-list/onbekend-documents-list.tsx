import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
  P,
} from "@maykin-ui/admin-ui";
import { useMemo } from "react";
import {
  useLoaderData,
  useParams,
  useSearchParams,
} from "react-router";
import { getPageFromSearchParams } from "~/lib";
import type { Document } from "~/types";

import type { onbekendDocumentsListLoader } from "./onbekend-documents-list.loader";

export function OnbekendDocumentsList() {
  const data = useLoaderData<typeof onbekendDocumentsListLoader>();
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, iotUuid } = useParams() as {
    serviceSlug: string | undefined;
    iotUuid: string | undefined;
  };

  const items = useMemo<ItemGridItemProps[]>(
    () =>
      data?.results?.map((doc: Document) => ({
        id: doc.uuid,
        title: doc.titel,
        icon: <Outline.DocumentIcon />,
        informationLines: [doc.identificatie].filter(Boolean),
        actions: [
          {
            as: "a" as const,
            children: <Outline.ArrowDownOnSquareIcon />,
            download: true,
            href: `/api/v1/services/${serviceSlug}/informatieobjecttypen/${iotUuid}/documents/${doc.uuid}/download`,
            title: "Bestand downloaden",
          },
        ],
      })) ?? [],
    [data?.results, serviceSlug, iotUuid],
  );

  if (!data) return null;

  return (
    <ItemGridTemplate
      title="Onbekend"
      itemGridProps={{ direction: "v", ellipsis: true, items }}
      paginatorProps={{
        count: data.count,
        page: getPageFromSearchParams(searchParams),
        pageSize: 20,
        onPageChange: (page) => setSearchParams({ page: page.toString() }),
      }}
    >
      <P>{data.count} documenten</P>
    </ItemGridTemplate>
  );
}
