import type { DecoratorFunction } from "storybook/internal/csf";

export const withCSRF: DecoratorFunction = (Story) => {
  return (
    <>
      <meta name="csrfmiddlewaretoken" content="INSECURE_FAKE_CSRF_TOKEN" />
      <Story />
    </>
  );
};
