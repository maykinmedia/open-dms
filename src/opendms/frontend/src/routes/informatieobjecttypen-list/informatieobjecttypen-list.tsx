import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
  P,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useMemo } from "react";
import { useLoaderData, useNavigate, useParams } from "react-router";
import type { InformatieObjectType } from "~/types";

import type { informatieobjecttypenListLoader } from "./informatieobjecttypen-list.loader";

export function InformatieObjectTypenList() {
  const data = useLoaderData<typeof informatieobjecttypenListLoader>();
  const navigate = useNavigate();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug } = useParams() as {
    serviceSlug: string | undefined;
  };

  const items = useMemo<ItemGridItemProps[]>(
    () =>
      data?.results?.map((iot: InformatieObjectType) => ({
        id: String(iot.uuid),
        title: iot.omschrijving,
        icon: <Outline.FolderIcon />,
        actions: [
          {
            as: "button" as const,
            "aria-label": iot.omschrijving,
            onClick: () => {
              invariant(serviceSlug);
              navigate(`/${serviceSlug}/onbekend/${iot.uuid}`);
            },
          },
        ],
      })) ?? [],
    [data?.results, serviceSlug, navigate],
  );

  if (!data) return null;

  return (
    <ItemGridTemplate
      title="Onbekend"
      itemGridProps={{ direction: "h", ellipsis: true, items }}
    >
      <P>{data.count} documenttypen</P>
    </ItemGridTemplate>
  );
}
