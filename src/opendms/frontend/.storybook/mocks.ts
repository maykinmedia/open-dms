import { HttpResponse, http } from "msw";
import type { ZaakType } from "~/types";

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
