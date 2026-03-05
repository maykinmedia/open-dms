import {
  H1,
  type ItemGridItemProps,
  type ItemGridProps,
} from "@maykin-ui/admin-ui";
import type { FC } from "react";
import { useLoaderData } from "react-router";
import type { documentsListLoader } from "~/routes/documents-list/documents-list.loader.ts";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();

  if (!data) return null;

  return (
    <div>
      <H1>Some very cool amazing fancy title</H1>
      <ItemGrid
        ellipsis
        items={data.results.map(
          (doc) =>
            ({
              title: doc.titel,
              icon: "📄",
              informationLines: [doc.formaat],
            }) satisfies ItemGridItemProps,
        )}
      />
    </div>
  );
};

const ItemGrid: FC<ItemGridProps> = ({ items }) => {
  return (
    <div>
      {items.map((item, idx) => (
        <div key={idx}>
          <div>{item.icon}</div>
          <div>{item.title}</div>
          <div>
            {item.informationLines?.map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
