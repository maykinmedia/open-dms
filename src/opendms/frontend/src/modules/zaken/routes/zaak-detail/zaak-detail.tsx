import {
  AttributeList,
  BaseTemplate,
  Body,
  Card,
  H2,
  type TypedField,
} from "@maykin-ui/admin-ui";
import { useLoaderData } from "react-router";
import type { Zaak } from "~/types";

import type { zaakDetailLoader } from "./zaak-detail.loader";

const FIELDS: TypedField<Zaak>[] = [
  { name: "identificatie", type: "string" },
  { name: "omschrijving", type: "string" },
  { name: "startdatum", type: "date" },
  { name: "registratiedatum", type: "date" },
  { name: "bronorganisatie", type: "string" },
  { name: "verantwoordelijkeOrganisatie", type: "string" },
  { name: "toelichting", type: "string" },
];

export function ZaakDetail() {
  const zaak = useLoaderData<typeof zaakDetailLoader>();

  return (
    <BaseTemplate>
      <Body>
        <Card>
          <H2>{zaak.identificatie}</H2>
          <AttributeList<Zaak> object={zaak} fields={FIELDS} />
        </Card>
      </Body>
    </BaseTemplate>
  );
}
