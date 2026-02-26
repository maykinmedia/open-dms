import {
  BaseTemplate,
  ConfigContext,
  H2,
  Hr,
  Logo,
  Outline,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import { Outlet, useNavigate } from "react-router";
import { apiClient } from "~/lib";

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
