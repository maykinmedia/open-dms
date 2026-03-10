import { HttpResponse, http } from "msw";
import type { ZaakType } from "~/types";

import { batchFactory, documentFactory, zaakFactory } from "./factories.ts";

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

export const MOCK_WHOAMI = http.post("/api/v1/accounts/whoami", () =>
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

export const MOCK_ZAAKTYPE = http.get(
  "/api/v1/services/service_2/zaaktypen/22222222-2222-2222-2222-222222222222",
  () =>
    HttpResponse.json({
      identificatie: "Zaaktype 2",
      uuid: "22222222-2222-2222-2222-222222222222",
      beginGeldigheid: "01-01-2020",
      eindeGeldigheid: "01-01-2026",
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

export const MOCK_DOCUMENTS = http.get(
  "/api/v1/services/exampleService/zaaktypen/exampleZaaktype/zaken/zaakYear/2026/zaakId/123",
  () =>
    HttpResponse.json({
      count: 300,
      previous: null,
      next: "/api/v1/services/exampleService/zaaktypen/exampleZaaktype/zaken/zaakYear/2026/zaakId/123?page=2",
      results: batchFactory(documentFactory, 20),
    }),
);
