import {
  BaseTemplate,
  ConfigContext,
  H2,
  Hr,
  Logo,
  type Option,
  Outline,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import type { FC } from "react";
import { Outlet, useLoaderData, useNavigate } from "react-router";
import { ServiceSelect } from "~/components/service-select/service-select.tsx";
import { apiRequest } from "~/lib";

/**
 * Represents a layout component tailored for unauthenticated users.
 *
 * @returns {JSX.Element} The rendered layout structure for the application.
 */
export const Layout = () => {
  return (
    <BaseTemplate primaryNavigationItems={[]} sidebarItems={[]} grid={true}>
      <ConfigContext.Provider
        value={{ templatesContentOnly: true, templatesGrid: false }}
      >
        <Outlet />
      </ConfigContext.Provider>
    </BaseTemplate>
  );
};

// TODO: From backend?
type authenticatedLayoutLoaderData = {
  serviceOptions: Option[];
};

export async function authenticatedLayoutLoader() {
  // TODO: Refine once API is clear, draft for now
  const response = await apiRequest<Response>("/api/v1/service/options", "GET");

  if (!response.ok) {
    throw new Response("Failed to load options", { status: response.status });
  }

  const serviceOptions: authenticatedLayoutLoaderData["serviceOptions"] =
    await response.json();
  return { serviceOptions };
}

/**
 * Represents a layout component tailored for authenticated users.
 *
 * @returns {JSX.Element} The rendered layout structure for the application.
 */
export const AuthenticatedLayout: FC = () => {
  const navigate = useNavigate();
  const { serviceOptions } = useLoaderData() as authenticatedLayoutLoaderData;

  const handleLogout = async () => {
    await apiRequest("/api/v1/accounts/logout");
    navigate("/login");
  };

  return (
    <BaseTemplate
      primaryNavigationItems={[
        <Logo abbreviated variant="contrast" key={"logo"} />,
        "spacer",
        {
          type: "button",
          title: "Uitloggen",
          children: <Outline.ArrowRightOnRectangleIcon />,
          onClick: handleLogout,
        },
      ]}
      sidebarItems={[
        <H2 key={"sidebar-h2"}>Open DMS</H2>,
        <Hr key={"sidebar-hr"} />,
        <ServiceSelect key="service-select" options={serviceOptions} />,
      ]}
    >
      <ConfigContext.Provider
        value={{
          templatesContentOnly: true,
          templatesGrid: false,
        }}
      >
        <Outlet />
      </ConfigContext.Provider>
    </BaseTemplate>
  );
};
