import { invariant } from "@maykin-ui/client-common";

type RequestMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "CONNECT"
  | "HEAD"
  | "OPTIONS"
  | "TRACE";

/**
 * Sends an HTTP request and returns the parsed JSON response.
 *
 * @param {string} path - The endpoint URL to send the request to.
 * @param {RequestMethod} [method="POST"] - The HTTP method to use for the request.
 * @param {FormData|unknown} [data] - The request payload or form data to be sent in the body of the request.
 * @param {AbortSignal} [signal] - An optional signal to abort the request.
 * @return {Promise<T>} A promise that resolves to the parsed JSON response of type T.
 * @throws {Response} Throws the response object if the request fails (response.ok is false).
 */
export async function apiRequest<T>(
  path: string,
  method: RequestMethod = "GET",
  data?: FormData | unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    method: method,
    headers: getRequestHeaders(method),
    body: getRequestBody(data),
    signal,
  });

  if (!response.ok) {
    throw response;
  }

  if (response.status === 204) return null as T; // No content
  return (await response.json()) as T;
}

/**
 * Generates and returns the appropriate request headers based on the HTTP method.
 *
 * @param {RequestMethod} method The HTTP request method (e.g., GET, POST, PUT).
 * @return {Record<string, string>} An object containing the headers for the request.
 *                                  Includes "Content-Type" as "application/json" by default.
 *                                  Adds "X-CSRFToken" for methods that require a CSRF token.
 */
function getRequestHeaders(method: RequestMethod): Record<string, string> {
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  // These requests do not require CSRF token.
  if (["GET", "HEAD", "CONNECT", "OPTIONS", "TRACE"].includes(method))
    return baseHeaders;

  // The token is obtaines using Django's {% csrf_token %}.
  const csrftoken = document.querySelector<HTMLInputElement>(
    "[name=csrfmiddlewaretoken]",
  )?.value;

  // Assert that the token is resolved.
  invariant(
    csrftoken,
    `CSRF token not found in template, are you requesting the page via Django?`,
  );

  // Return the token along with the base headers.
  return { ...baseHeaders, "X-CSRFToken": csrftoken };
}

/**
 * Converts the provided data into a JSON string representation if it is defined.
 * If the data is an instance of FormData, it is transformed into an object before stringification.
 *
 * @param {FormData | unknown} data - The input data to be processed. Can either be a FormData instance or any other data type.
 * @return {string | undefined} The JSON string representation of the input data, or undefined if the input data is not provided.
 */
function getRequestBody(data: FormData | unknown): string | undefined {
  const _data = data instanceof FormData ? Object.fromEntries(data) : data;
  return data ? JSON.stringify(_data) : undefined;
}
