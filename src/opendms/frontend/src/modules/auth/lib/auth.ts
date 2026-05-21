import { apiClient } from "~/lib";

/**
 * Performs a logout operation by sending a GET request to the
 * logout endpoint of the API.
 *
 * This function is used to terminate the current user session
 * on the server side. It communicates with the API's logout
 * URL and ends the user's authentication state.
 *
 * @returns {Promise} A Promise that resolves when the server
 *          successfully processes the logout request.
 */
export const logout = () => apiClient.GET("/api/v1/accounts/logout");
