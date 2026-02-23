export type User = {
  pk: number;
  email: string;
  firstName: string;
  lastName: string;
  username: string;
};

export type ValidationErrors = {
  nonFieldErrors: string[];
  [index: string]: string[];
};
