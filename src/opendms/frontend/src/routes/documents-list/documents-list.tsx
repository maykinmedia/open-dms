import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
} from "@maykin-ui/admin-ui";
import { useMemo } from "react";
import { useLoaderData, useSearchParams } from "react-router";
import { getPageFromSearchParams } from "~/lib";
import type { documentsListLoader } from "~/routes/documents-list/documents-list.loader.ts";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();
  const [searchParams, setSearchParams] = useSearchParams();

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

  return (
    <ItemGridTemplate
      title="Some very cool amazing fancy title"
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
