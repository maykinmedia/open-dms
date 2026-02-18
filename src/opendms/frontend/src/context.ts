import { createContext } from "react-router";

export interface User {
  id: string;
  email: string;
}

// Simple context defining user. TODO: Expand or implement elsewhere
export const userContext = createContext<User | null>(null);
