import {
  type FormField,
  LoginTemplate,
  type TypedSerializedFormData,
} from "@maykin-ui/admin-ui";
import type { FormEvent } from "react";
import { type SubmitTarget, useActionData, useSubmit } from "react-router";
import type { ValidationErrors } from "~/types";

type LoginFormType = TypedSerializedFormData<"username" | "password">;

const LOGIN_FORM_FIELDS: FormField[] = [
  { name: "username", label: "Gebruikersnaam", type: "text" },
  { name: "password", label: "Wachtwoord", type: "password" },
];

/**
 * Renders the LoginComponent component, which displays a login form for user authentication.
 *
 * @return {JSX.Element} The LoginComponent component containing a form with fields for username and password.
 */
export function Login() {
  const validationErrors = useActionData<ValidationErrors>();
  const submit = useSubmit();

  const handleSubmit = (_: FormEvent<HTMLFormElement>, data: LoginFormType) => {
    void submit(data as SubmitTarget, { method: "post" });
  };

  return (
    <LoginTemplate<LoginFormType>
      formProps={{
        fields: LOGIN_FORM_FIELDS,
        labelSubmit: "Inloggen",
        nonFieldErrors: validationErrors?.nonFieldErrors,
        onSubmit: handleSubmit,
      }}
    />
  );
}
