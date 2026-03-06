import {
  BodyBaseTemplate,
  H1,
  ItemGrid,
  type ItemGridItemProps,
  Outline,
} from "@maykin-ui/admin-ui";
import { useLoaderData } from "react-router";
import type { documentsListLoader } from "~/routes/documents-list/documents-list.loader.ts";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();

  if (!data) return null;

  return (
    <BodyBaseTemplate>
      <H1>Some very cool amazing fancy title</H1>
      <ItemGrid
        ellipsis
        items={data.results.map(
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
        )}
      />
    </BodyBaseTemplate>
  );
};
