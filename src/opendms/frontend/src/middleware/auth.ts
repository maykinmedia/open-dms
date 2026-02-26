import { type MiddlewareFunction, redirect } from "react-router";
import { apiClient } from "~/lib";

import { userContext } from "../context.ts";

/**
 * Middleware that checks if a user is authenticated and/or has correct roles
 * before either allowing or disallowing entry to the route
 */
export const authRouterMiddleware: MiddlewareFunction<unknown> = async (
  { context },
  next,
) => {
  const { data: whoAmI } = await apiClient.GET("/api/v1/accounts/whoami");

  if (!whoAmI?.isAuthenticated) {
    throw redirect("/login");
  }

  context.set(userContext, whoAmI.user);
  await next();
};
