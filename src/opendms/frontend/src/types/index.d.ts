import type { components } from "~/types/schema.d.ts";

export * from "./schema.d.ts";

// Aliases
export type User = components["schemas"]["User"];

export type Document = components["schemas"]["Document"];

export type ZaakType = components["schemas"]["ZaakType"];
export type Zaak = components["schemas"]["Zaak"];

export type Fout = components["schemas"]["Fout"];
export type ValidatieFout = components["schemas"]["ValidatieFout"];
