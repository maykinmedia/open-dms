import {
  type FormField,
  LoginTemplate,
  type TypedSerializedFormData,
} from "@maykin-ui/admin-ui";
import type { FormEvent } from "react";
import { type SubmitTarget, useSubmit } from "react-router";

type LoginFormType = TypedSerializedFormData<"username" | "password">;

/**
 * Renders the LoginComponent component, which displays a login form for user authentication.
 *
 * @return {JSX.Element} The LoginComponent component containing a form with fields for username and password.
 */
export function Login() {
  const submit = useSubmit();

  const fields: FormField[] = [
    { name: "username", label: "Gebruikersnaam", type: "text" },
    { name: "password", label: "Wachtwoord", type: "password" },
  ];

  const handleSubmit = (_: FormEvent<HTMLFormElement>, data: LoginFormType) => {
    void submit(data as SubmitTarget, { method: "post" });
  };

  return (
    <LoginTemplate<LoginFormType>
      formProps={{ fields, labelSubmit: "Inloggen", onSubmit: handleSubmit }}
    />
  );
}
