import type { SearchResult } from "@maykin-ui/admin-ui";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { initialize, mswLoader } from "msw-storybook-addon";
import { withRouter } from "storybook-addon-remix-react-router";
import { GlobalSearchButton } from "~/components";

import { withCSRF } from "../../../.storybook/decorators";
import { MOCK_SEARCH } from "../../../.storybook/mocks";
import { sanitizedReactRouterParameters } from "../../../.storybook/utils";

initialize();

const meta: Meta<typeof GlobalSearchButton> = {
  title: "Components/GlobalSearch",
  component: GlobalSearchButton,
  decorators: [withRouter, withCSRF],
  loaders: [mswLoader],
  parameters: {
    reactRouter: sanitizedReactRouterParameters(),
    msw: { handlers: [MOCK_SEARCH] },
  },
};

export default meta;

type Story = StoryObj<typeof GlobalSearchButton>;

const MOCK_RESULTS: SearchResult[] = [
  {
    title: "Aanvraag vergunning 2024-001",
    href: "/service_1/11111111-1111-1111-1111-111111111111/2024/1",
    subtitle: "aanvraag-vergunning.pdf",
    group: "Documenten",
  },
  {
    title: "Besluit vergunning 2024-002",
    href: "/service_1/11111111-1111-1111-1111-111111111111/2024/2",
    subtitle: "besluit.pdf",
    group: "Documenten",
  },
  {
    title: "Correspondentie 2024-003",
    href: "/service_1/11111111-1111-1111-1111-111111111111/2024/3",
    subtitle: "brief.docx",
    group: "Documenten",
  },
];

export const Default: Story = {
  args: {
    search: async () => MOCK_RESULTS,
  },
};
