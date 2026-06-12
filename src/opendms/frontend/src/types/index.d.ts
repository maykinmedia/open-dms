import type { components } from "~/types/schema.d.ts";

export * from "./schema.d.ts";

// Aliases
export type User = components["schemas"]["User"];

export type Document = components["schemas"]["Document"];

export type StatusType = components["schemas"]["StatusType"];

export type ZaakType = components["schemas"]["ZaakType"];

// Deliberately remove _expand from schema as there is no sensible type for the
// dynamic nature. Whenever used: _expand should be parsed to obtain the type.
export type Zaak = Omit<components["schemas"]["Zaak"], "_expand">;

export type Fout = components["schemas"]["Fout"];
export type ValidatieFout = components["schemas"]["ValidatieFout"];
