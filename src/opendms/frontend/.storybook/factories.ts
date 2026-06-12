import type { Document, StatusType, Zaak } from "~/types";

type FactoryFn<T extends object> = (values?: Partial<T>) => T;

export const documentFactory = createFactory<Document>({
  hasPendingUpdates: false,
  identificatie: "doc-{index}",
  titel: "Document {index}",
  bestandsnaam: "document-{index}.pdf",
  beschrijving: null,
  formaat: "pdf",
  link: null,
  auteur: "",
  beginRegistratie: "",
  bronorganisatie: "",
  creatiedatum: "",
  informatieobjecttype: "",
  inhoud: "",
  taal: "",
  url: "",
  uuid: "",
});

export const statustypeFactory = createFactory<StatusType>({
  uuid: "00000000-0000-0000-0000-000000000000",
  url: "http://www.example.com/api/v1/services/catalogi-api/statustypen/00000000-0000-0000-0000-000000000000",
  catalogus: "",
  informeren: false,
  isEindstatus: false,
  omschrijving: "Sed do eiusmod",
  volgnummer: 0,
  zaaktype: "",
  zaaktypeIdentificatie: "",
});

export const zaakFactory = createFactory<Zaak>({
  identificatie: "ZAAK-2026-0000000010",
  omschrijving: "Lorem ipsum dolor sit amet",
  uuid: "00000000-0000-0000-0000-000000000000",
  bronorganisatie: "",
  registratiedatum: "",
  startdatum: "",
  toelichting: "",
  url: "http://www.example.com/zaken/api/v1/zaken/00000000-0000-0000-0000-000000000000",
  verantwoordelijkeOrganisatie: "",
  zaaktype:
    "http://www.example.com/catalogi/api/v1/zaaktypen/22222222-2222-2222-2222-222222222222",
});

/**
 * Creates a factory function for `<T>`.
 * @param fixture The base fixture to return when calling the produced factory function.
 * @return {FactoryFn} A function that takes `values` and assigns it to a cloned `fixture` (supplied by `createFactory`)
 * before returning it.
 */
function createFactory<T extends object>(fixture: T): FactoryFn<T> {
  return (values) => baseFactory(fixture, values);
}

/**
 * Creates `amount` instances of `<T>` using provided `factoryFn`.
 * @param {FactoryFn} factoryFn A function that takes `values` and assigns it to a cloned `fixture` (supplied by
 * `createFactory`) before returning it.
 * @param {number} amount
 * @param {Partial<T>|Partial<T>[]} values A (subset of) `<T>` object.
 */
export function batchFactory<T extends object>(
  factoryFn: FactoryFn<T>,
  amount: number,
  values?: Partial<T> | Partial<T>[],
): T[] {
  const valuesArray = Array.from({
    ...(Array.isArray(values) ? values : []),
    length: amount,
  });
  return valuesArray.map((_values, index) => {
    const object = factoryFn(_values || values);

    return Object.fromEntries(
      Object.entries(object).map(([key, value]) => {
        const newValue =
          typeof value === "string"
            ? value.replaceAll("{index}", (index + 1).toString())
            : value;
        return [key, newValue];
      }),
    ) as T;
  });
}

/**
 * The base factory function, creates an instance of `<T>` with values assigns to it.
 * Takes `values` and assigns it to a cloned `fixture` before returning it.
 * @private Don't use this directly, use `fooFactory = createFactory<Foo>({'foo': 'bar'})` instead.
 * @param fixture
 * @param values
 */
export function baseFactory<T extends object>(
  fixture: T,
  values?: Partial<T>,
): T {
  const clone = { ...fixture }; // Shallow clone for now.
  return Object.assign(clone, values || {});
}
