import {
  BaseTemplate,
  ConfigContext,
  Logo,
  ModalService,
  Outline,
  Sidebar,
  Toolbar,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import { Outlet, useNavigate, useNavigation } from "react-router";
import { ServiceSelect, YearSelect, ZaaktypeSelect } from "~/components";
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
  const { state } = useNavigation();

  const handleLogout = async () => {
    await apiClient.GET("/api/v1/accounts/logout");
    navigate("/login");
  };

  return (
    <ModalService>
      <BaseTemplate
        primaryNavigationItems={[
          <Logo abbreviated key={"logo"} />,
          "spacer",
          state !== "idle" ? (
            <Outline.ArrowPathIcon
              key="loading"
              aria-label={"Bezig met laden"}
              spin
            />
          ) : undefined,
          {
            type: "button",
            title: "Uitloggen",
            children: <Outline.ArrowRightOnRectangleIcon />,
            onClick: handleLogout,
          },
        ]}
        // Use slot to prevent unnecessary re-renders.
        slotSidebar={
          <Sidebar>
            <Toolbar
              align="space-between"
              direction="vertical"
              pad={true}
              variant="transparent"
            >
              <ServiceSelect key="service-select" />
              <ZaaktypeSelect key="zaaktype-select" />
              <YearSelect key="year-select" />
            </Toolbar>
          </Sidebar>
        }
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
    </ModalService>
  );
};
