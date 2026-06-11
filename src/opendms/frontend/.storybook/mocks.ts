import { HttpResponse, http } from "msw";
import type { ZaakType } from "~/types";

import {
  batchFactory,
  documentFactory,
  statustypeFactory,
  zaakFactory,
  zaakWithStatusFactory,
} from "./factories.ts";

//
// accounts
//

export const MOCK_CORRECT_LOGIN = http.post("/api/v1/accounts/login", () =>
  HttpResponse.json({
    isAuthenticated: true,
    user: {
      pk: 1,
      email: "johndoe@example.com",
      firstName: "John",
      lastName: "Doe",
      username: "johndoe",
    },
  }),
);

export const MOCK_INCORRECT_LOGIN = http.post("/api/v1/accounts/login", () =>
  HttpResponse.json(
    {
      nonFieldErrors: ["Kan niet inloggen met de opgegeven gegevens.\n"],
    },
    { status: 400 },
  ),
);

export const MOCK_WHOAMI = http.get("/api/v1/accounts/whoami", () =>
  HttpResponse.json({
    isAuthenticated: true,
    user: {
      pk: 1,
      email: "johndoe@example.com",
      firstName: "John",
      lastName: "Doe",
      username: "johndoe",
    },
  }),
);

// search...

export const MOCK_SEARCH = http.post("/api/v1/search", () =>
  HttpResponse.json({
    count: 0,
    results: [],
  }),
);

//
// services
//

export const MOCK_SERVICE_OPTIONS = http.get("/api/v1/services", () =>
  HttpResponse.json({
    results: [
      { label: "Service 1", slug: "service_1" },
      { label: "Service 2", slug: "service_2" },
    ],
  }),
);

export const MOCK_ZAAKTYPE_OPTIONS = http.get(
  "/api/v1/services/:serviceSlug/zaaktypen",
  () =>
    HttpResponse.json({
      results: [
        {
          identificatie: "Zaaktype 1",
          uuid: "11111111-1111-1111-1111-111111111111",
        },
        {
          identificatie: "Zaaktype 2",
          uuid: "22222222-2222-2222-2222-222222222222",
        },
      ],
    }),
);

export const MOCK_ZAAKTYPEN = http.get(
  "/api/v1/services/service_2/zaaktypen",
  () =>
    HttpResponse.json({
      count: 2,
      previous: "http://...",
      next: "http://...",
      results: [
        {
          identificatie: "Zaaktype 1",
          omschrijving: "Zaaktype 1",
          uuid: "11111111-1111-1111-1111-111111111111",
          versiedatum: "2020-01-01",
          beginGeldigheid: "2020-01-01",
          eindeGeldigheid: "2026-01-01",
        },
        {
          identificatie: "Zaaktype 2",
          omschrijving: "Zaaktype 2",
          uuid: "22222222-2222-2222-2222-222222222222",
          versiedatum: "2020-01-01",
          beginGeldigheid: "2020-01-01",
          eindeGeldigheid: "2026-01-01",
        },
      ],
    }),
);

export const MOCK_ZAAKTYPE = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222",
  () =>
    HttpResponse.json({
      identificatie: "Zaaktype 2",
      omschrijving: "Zaaktype 2",
      uuid: "22222222-2222-2222-2222-222222222222",
      url: "http://example.com/zaaktypen/22222222-2222-2222-2222-222222222222",
      concept: false,
      catalogus: "",
      versiedatum: "2020-01-01",
      beginGeldigheid: "2020-01-01",
      eindeGeldigheid: "2026-01-01",
    } as Partial<ZaakType>),
);

/**
 * Mocked API response for retrieving "zaken" (cases) for a specific "zaaktype" (case type).
 *
 * This variable simulates the behavior of an HTTP GET request to fetch paginated and filtered results
 * based on query parameters. It returns a JSON response with metadata (`count`, `previous`, `next`) and
 * a list of results (`results`).
 *
 * Features:
 * - Pagination: Supports the `page` query parameter to navigate between pages of results.
 * - Filtering: Supports the `identificatie__icontains` and `omschrijving` query parameters for filtering
 *   results based on `identificatie` or `omschrijving` fields.
 *
 * Query Parameters:
 * - `page`: Specifies the page to retrieve (default is 1).
 * - `identificatie__icontains`: A case-insensitive substring match filter for the `identificatie` field.
 * - `omschrijving`: A case-insensitive substring match filter for the `omschrijving` field.
 *
 * Response:
 * - `count`: Total number of filtered items.
 * - `previous`: URL to the previous page of results or `null` if on the first page.
 * - `next`: URL to the next page of results or `null` if on the last page.
 * - `results`: Array of filtered and paginated "zaken" objects.
 *
 * Example Behavior:
 * - If there are 3 pages, each with a page size of 100, the total number of items is 250.
 * - Filters and pagination parameters impact the results dynamically.
 */
export const MOCK_ZAKEN = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/zaken",
  ({ request }) => {
    const pages = 3;
    const pageSize = 100;
    const count = pages * pageSize - 50;

    const url = new URL(request.url);
    const urlSearchParams = new URLSearchParams(url.search);
    const page = parseInt(urlSearchParams.get("page") || "1");
    const page0 = page - 1;

    const results = batchFactory(zaakFactory, count, {
      identificatie: "zaak-{index}",
    }).filter((zaak, index) => {
      if (index >= page0 * pageSize && index < page0 * pageSize + pageSize) {
        const identificatieFilter = urlSearchParams
          .get("identificatie__icontains")
          ?.toLowerCase();

        const omschrijvingFilter = urlSearchParams
          .get("omschrijving")
          ?.toLowerCase();

        const matchIdentificatie = identificatieFilter
          ? zaak.identificatie?.toLowerCase().includes(identificatieFilter)
          : true;

        const matchOmschrijving = omschrijvingFilter
          ? zaak.omschrijving?.toLowerCase().includes(omschrijvingFilter)
          : true;

        return matchIdentificatie && matchOmschrijving;
      }
    });

    return HttpResponse.json({
      count,
      previous: "http://...",
      next: "http://...",
      results,
    });
  },
);

export const MOCK_STATUSTYPEN = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/statustypen",
  () =>
    HttpResponse.json({
      count: 3,
      results: [
        statustypeFactory({
          uuid: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
          url: "http://example.com/statustypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
          omschrijving: "Ontvangen",
          volgnummer: 1,
        }),
        statustypeFactory({
          uuid: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
          url: "http://example.com/statustypen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
          omschrijving: "In Behandeling",
          volgnummer: 2,
        }),
        statustypeFactory({
          uuid: "cccccccc-cccc-cccc-cccc-cccccccccccc",
          url: "http://example.com/statustypen/cccccccc-cccc-cccc-cccc-cccccccccccc",
          omschrijving: "Afronden",
          volgnummer: 3,
          isEindstatus: true,
        }),
      ],
    }),
);

export const MOCK_ZAKEN_WITH_STATUS = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/zaken",
  () => {
    // statustype is a URI — must match url in MOCK_STATUSTYPEN
    const statustypeUrls = [
      null,
      "http://example.com/statustypen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "http://example.com/statustypen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "http://example.com/statustypen/cccccccc-cccc-cccc-cccc-cccccccccccc",
    ];

    const results = batchFactory(zaakWithStatusFactory, 12, {
      identificatie: "ZAAK-2026-{index}",
    }).map((zaak, index) => ({
      ...zaak,
      statustype: statustypeUrls[index % statustypeUrls.length],
    }));

    return HttpResponse.json({ count: 12, results });
  },
);

export const MOCK_CREATE_STATUS = http.post(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/zaken/:zaakUuid/statussen",
  () => HttpResponse.json({}, { status: 201 }),
);

export const MOCK_CREATE_ZAAK = http.post(
  "/api/v1/services/service_2/zaken",
  () => HttpResponse.json(zaakWithStatusFactory(), { status: 201 }),
);

export const MOCK_ZAAK = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/zaken/123",
  () => HttpResponse.json(zaakFactory()),
);

export const MOCK_DOCUMENTS = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222/zaken/123/documents",
  ({ request }) => {
    const pageSize = 20;
    const count = 300;

    const url = new URL(request.url);
    const page = parseInt(new URLSearchParams(url.search).get("page") || "1");
    const page0 = page - 1;

    const results = batchFactory(documentFactory, count).slice(
      page0 * pageSize,
      page0 * pageSize + pageSize,
    );

    return HttpResponse.json({
      count,
      previous: "http://...",
      next: "http://...",
      results,
    });
  },
);
