import { type MiddlewareFunction, redirect } from "react-router";
import { apiRequest } from "~/lib";

import { userContext } from "../context.ts";

/**
 * Middleware that checks if a user is authenticated and/or has correct roles
 * before either allowing or disallowing entry to the route
 */
export const authMiddleware: MiddlewareFunction<unknown> = async (
  { context },
  next,
) => {
  const whoAmI = await apiRequest<{
    isAuthenticated: boolean;
    user: object | null;
  }>("/api/v1/accounts/whoami", "GET");

  if (!whoAmI.isAuthenticated) {
    throw redirect("/login");
  }

  context.set(userContext, whoAmI.user);
  await next();
};
