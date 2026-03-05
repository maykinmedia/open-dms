import type { components } from "~/types/schema.d.ts";

export * from "./schema.d.ts";

// Aliases
export type User = components["schemas"]["User"];
export type ValidatieFout = components["schemas"]["ValidatieFout"];
export type ZaakType = components["schemas"]["ZaakType"];

// TODO
export type Zaak = {
  identificatie: string;
  omschrijving: string;
};

// TODO Link to `schema.d.ts` or something
export type Document = {
  identificatie: string;
  titel: string;
  bestandsnaam?: string | null;
  beschrijving?: string | null;
  formaat?: string | null;
  link?: string | null;
};
