import { type MiddlewareFunction, redirect } from "react-router";

import { type User, userContext } from "../context.ts";

/**
 * Middleware that checks if a user is authenticated and/or has correct roles
 * before either allowing, or disallowing entry to the route
 */
export const authMiddleware: MiddlewareFunction<unknown> = async (
  { context },
  next,
) => {
  // TODO: Replace with real session/user api call/check
  const user: User | null = null;

  if (!user) {
    throw redirect("/");
  }

  context.set(userContext, user);

  await next();
};
