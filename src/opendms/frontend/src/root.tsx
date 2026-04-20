import {
  BaseTemplate,
  ConfigContext,
  Logo,
  Outline,
  type SearchResult,
  Sidebar,
  Toolbar,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import type { MouseEventHandler } from "react";
import { Outlet, useNavigate, useNavigation } from "react-router";
import {
  GlobalSearchButton,
  ServiceSelect,
  YearSelect,
  ZaaktypeSelect,
} from "~/components";
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

  const handleLogoClick: MouseEventHandler = (e) => {
    e.preventDefault();
    return navigate("/");
  };

  const handleLogout = async () => {
    await apiClient.GET("/api/v1/accounts/logout");
    navigate("/login");
  };

  const handleSearch = async (
    query: string,
    { signal }: { signal: AbortSignal },
  ): Promise<SearchResult[]> => {
    if (!query.trim()) return [];
    const { data } = await apiClient.POST("/api/v1/search", {
      body: { query, page: 1, pageSize: 10, sort: "relevance" },
      signal,
    });
    const results = data?.results ?? [];
    return results.flatMap((item) => {
      if (item.type === "zaak") {
        const {
          uuid,
          identificatie,
          startdatum,
          omschrijving,
          ztcServiceSlug,
          ztcUuid,
          startjaar,
        } = item.data;
        if (!ztcServiceSlug || !ztcUuid) return [];
        const zaakYear = startjaar ?? new Date(startdatum).getFullYear();
        return [
          {
            title: omschrijving || identificatie,
            href: `/${ztcServiceSlug}/${ztcUuid}/${zaakYear}/${uuid}`,
            icon: <Outline.FolderIcon />,
            group: "Zaken",
          },
        ];
      }

      const zaak = item.data.zaakReferenties?.[0];
      if (!zaak?.ztcServiceSlug || !zaak.ztcUuid) return [];
      const zaakYear =
        zaak.startjaar ?? new Date(zaak.startdatum).getFullYear();
      return [
        {
          title: item.data.titel,
          href: `/${zaak.ztcServiceSlug}/${zaak.ztcUuid}/${zaakYear}/${zaak.uuid}?highlight=${item.data.uuid}`,
          icon: <Outline.DocumentIcon />,
          subtitle: item.data.bestandsnaam ?? undefined,
          group: "Documenten",
        },
      ];
    });
  };

  return (
    <BaseTemplate
      primaryNavigationItems={[
        <Logo abbreviated key={"logo"} href="/" onClick={handleLogoClick} />,
        <GlobalSearchButton key="global-search" search={handleSearch} />,
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
  );
};
