import { type ActionFunctionArgs, redirect } from "react-router";
import { apiClient } from "~/lib";

/**
 * Handles the login action by submitting user credentials to the API and redirecting upon success.
 *
 * @param {Object} params - The parameters for the action function.
 * @param {ActionFunctionArgs} params.request - The request object containing form data.
 * @return {Promise<Response>} The redirection response object after successful login.
 */
export async function loginAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const username = formData.get("username") || "";
  const password = formData.get("password") || "";

  const { error } = await apiClient.POST("/api/v1/accounts/login", {
    body: {
      username: username.toString(),
      password: password.toString(),
    },
  });

  return error ? error : redirect("/");
}
