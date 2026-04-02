import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
  P,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useMemo } from "react";
import {
  useLoaderData,
  useParams,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import { getPageFromSearchParams } from "~/lib";
import { authenticatedRootLoader } from "~/routes/authenticated-root.loader.ts";
import type { documentsListLoader } from "~/routes/documents-list/documents-list.loader.ts";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid, zaakYear, zaakId } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
    zaakYear: string | undefined;
    zaakId: string | undefined;
  };
  const rootData =
    useRouteLoaderData<typeof authenticatedRootLoader>("authenticated-root");

  const items = useMemo<ItemGridItemProps[]>(() => {
    return (
      data?.results.map((doc) => {
        return {
          title: doc.titel,
          icon: <Outline.DocumentIcon />,
          informationLines: [doc.formaat],
          actions: [
            {
              as: "a",
              download: true,
              href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/download`,
            },
          ],
        };
      }) ?? []
    );
  }, [data?.results, serviceSlug, zaaktypeUuid, zaakId]);

  if (!data) return null;
  invariant(rootData?.zaaktype?.identificatie, "Zaaktype not loaded!");

  return (
    <ItemGridTemplate
      title={`${rootData.zaaktype.identificatie} / ${zaakYear} / documenten`}
      itemGridProps={{ ellipsis: true, items }}
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
};
