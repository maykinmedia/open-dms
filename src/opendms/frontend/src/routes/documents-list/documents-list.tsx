import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
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
  const { zaakYear } = useParams() as {
    zaakYear: string | undefined;
  };
  const rootData =
    useRouteLoaderData<typeof authenticatedRootLoader>("authenticated-root");

  const items = useMemo(
    () =>
      data?.results.map(
        (doc) =>
          ({
            title: doc.titel,
            icon: <Outline.DocumentIcon />,
            informationLines: [doc.formaat],
            buttonProps: {
              as: "a",
              href: doc.link ?? "#",
              download: doc.titel,
            },
          }) satisfies ItemGridItemProps,
      ) ?? [],
    [data?.results],
  );

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
    />
  );
};
