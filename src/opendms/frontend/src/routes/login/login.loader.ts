import { apiClient } from "~/lib";

/**
 * Makes sure the CSRF-cookie is available.
 */
export async function loginLoader() {
  await apiClient.GET("/accounts/whoami");
}
