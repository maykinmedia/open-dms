import { invariant } from "@maykin-ui/client-common";

const REGEX_UUID =
  /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/;

/**
 * Extracts a UUID from the given URL string.
 *
 * @param {string} url - The URL string from which to extract the UUID.
 * @return {string} The extracted UUID, if present and valid.
 * @throws {Error} Throws an error if no valid UUID is found in the URL.
 */
export function getUUIDFromUrl(url: string): string {
  invariant(url.length, "Url is empty!");
  const uuid = url.split("/").pop();
  invariant(uuid && uuid.match(REGEX_UUID), `No UUID found in URL: ${url}!`);
  return uuid;
}
