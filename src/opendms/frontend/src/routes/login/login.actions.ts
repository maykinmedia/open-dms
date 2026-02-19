import { type ActionFunctionArgs, redirect } from "react-router";
import { apiRequest } from "~/lib";

/**
 * Handles the login action by submitting user credentials to the API and redirecting upon success.
 *
 * @param {Object} params - The parameters for the action function.
 * @param {ActionFunctionArgs} params.request - The request object containing form data.
 * @return {Promise<Response>} The redirection response object after successful login.
 */
export async function loginAction({
  request,
}: ActionFunctionArgs): Promise<Response> {
  const formData = await request.formData();
  await apiRequest<{ user: unknown }>(
    "/api/v1/accounts/login",
    "POST",
    formData,
  );
  return redirect("/");
}
