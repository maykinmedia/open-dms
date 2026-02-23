import type { DecoratorFunction } from "storybook/internal/csf";

export const withCSRF: DecoratorFunction = (Story) => {
  return (
    <>
      <input
        name="csrfmiddlewaretoken"
        type="hidden"
        value="INSECURE_FAKE_CSRF_TOKEN"
      />
      <Story />
    </>
  );
};
