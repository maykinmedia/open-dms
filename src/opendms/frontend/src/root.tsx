import {
  BaseTemplate,
  ConfigContext,
  H2,
  Hr,
  type LoadOptionsFn,
  Logo,
  type Option,
  Outline,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import { Outlet, useNavigate } from "react-router";
import { apiClient } from "~/lib";

import { ServiceSelect } from "./components/service-select/service-select";

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

/**
 * Represents a layout component tailored for authenticated users.
 *
 * @returns {JSX.Element} The rendered layout structure for the application.
 */
export const AuthenticatedLayout = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await apiClient.GET("/api/v1/accounts/logout");
    navigate("/login");
  };

  /**
   * Fetches the service options from the backend (client-side)
   * Accepts string as first parameter according to `@maykin-ui / LoadOptionsFn` and returns a Promise of results
   * @param search
   */
  const getServiceOptions: LoadOptionsFn = async (
    search,
  ): Promise<Option[]> => {
    const { data } = await apiClient.GET("/api/v1/services", {
      params: {
        query: {
          search,
        },
      },
    });

    if (!data) {
      return [];
    }

    return data.results.map(({ label, slug }) => ({
      label,
      value: slug,
    }));
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
        <ServiceSelect key="service-select" options={getServiceOptions} />,
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
