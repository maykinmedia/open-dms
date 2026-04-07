import { invariant } from "@maykin-ui/client-common";
import createClient, { type Middleware } from "openapi-fetch";
import type { Fout, ValidatieFout, paths } from "~/types";

/**
 * Middleware that ensures the "Content-Type" header is set to "application/json" for outgoing requests.
 *
 * This middleware modifies the request's headers by adding or overriding the "Content-Type" field
 * with the value "application/json". This is useful for guaranteeing that the request is sent
 * with the appropriate content type for JSON payloads.
 *
 * @type {Middleware}
 */
const contentTypeJSONMiddleware: Middleware = {
  async onRequest({ request }) {
    request.headers.set("Content-Type", "application/json");
  },
};

/**
 * Middleware responsible for handling client-side CSRF protection by automatically
 * attaching a CSRF token to the headers of HTTP requests that require it.
 *
 * This middleware fetches the CSRF token from an input field added via Django templates
 * (using the `{% csrf_token %}` template tag) and ensures it is included in the
 * `X-CSRFToken` header of requests. It will only attach the token for methods that
 * modify server-side state (e.g., "POST", "PUT", "DELETE", etc.).
 *
 * Note:
 * - Requests with HTTP methods such as "GET", "HEAD", "CONNECT", "OPTIONS", and "TRACE"
 *   are considered to not require a CSRF token and will not include the header.
 * - The middleware will throw an error if the CSRF token cannot be found, indicating
 *   that the page might not have been rendered through Django or the token was not
 *   correctly embedded.
 *
 * Middleware type: {@link Middleware}
 */
const csrfClientMiddleware: Middleware = {
  async onRequest({ request }) {
    // These requests do not require CSRF token.
    if (["GET", "HEAD", "CONNECT", "OPTIONS", "TRACE"].includes(request.method))
      return;

    // The token is obtaines using Django's {% csrf_token %}.
    const csrftoken = document.querySelector<HTMLMetaElement>(
      "[name=csrfmiddlewaretoken]",
    )?.content;

    // Assert that the token is resolved.
    invariant(
      csrftoken,
      `CSRF token not found in template, are you requesting the page via Django?`,
    );

    request.headers.set("X-CSRFToken", csrftoken);
  },
};

/**
 * An instance of the API client created using the `createClient` function.
 * The client is configured with the base URL derived from the current window's origin.
 *
 * This client is used for making HTTP requests to interact with the server-side API
 * and adheres to the defined paths structure for endpoint typing and safety.
 */
export const apiClient = createClient<paths>({
  // This is needed to make sure on development our proxy works, whilst in production we do want the location's URL
  baseUrl: import.meta.env.DEV ? "" : window.location.origin,
});
apiClient.use(contentTypeJSONMiddleware);
apiClient.use(csrfClientMiddleware);

export type FormErrors = {
  nonFieldErrors: string | undefined;
  errors: Record<string, string>;
};

/**
 * For endpoints optionally returning `Fout`, this can be used to create
 * an object containing `nonFieldErrors` and `errors`. These can be passed to form
 * instances to show meaningful error messages.
 *
 * If `fout` satisfies `ValidatieFout`, the result of `validatieFout2FormErrors`
 * is returned.
 *
 * @param fout
 */
export function fout2FormErrors(fout: Fout | undefined): FormErrors {
  if (fout && ("nonFieldErrors" in fout || "invalidParams" in fout)) {
    return validatieFout2FormErrors(fout as ValidatieFout);
  }
  return {
    nonFieldErrors: fout?.detail,
    errors: {},
  };
}

/**
 * For endpoints optionally returning `ValidatieFout`, this can be used to create
 * an object containing `nonFieldErrors` and `errors`. These can be passed to form
 * instances to show meaningful error messages.
 * @param validatieFout
 */
export function validatieFout2FormErrors(
  validatieFout: ValidatieFout | undefined,
): FormErrors {
  const invalidParams = validatieFout?.invalidParams || [];
  const nonFieldErrors = invalidParams.find(
    ({ name }) => name === "nonFieldErrors",
  )?.reason;
  const errors = invalidParams
    .filter(({ name }) => name !== "nonFieldErrors")
    .reduce((acc, { name, reason }) => ({ ...acc, [name]: reason }), {});

  return { nonFieldErrors, errors };
}

/**
 * Retrieves the current page number from the provided URL search parameters.
 *
 * @param {URLSearchParams} searchParams - The URL search parameters to extract the page number from.
 * @return {number} The page number. If the page parameter is not present, invalid, or less than 1, defaults to 1.
 */
export function getPageFromSearchParams(searchParams: URLSearchParams): number {
  const raw = searchParams.get("page");
  const parsed = parseInt(raw ?? "1");
  return isNaN(parsed) || parsed < 1 ? 1 : parsed;
}
