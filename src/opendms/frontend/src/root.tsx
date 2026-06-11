import {
  BaseTemplate,
  Button,
  ConfigContext,
  Logo,
  ModalService,
  Outline,
  type SearchResult,
  Sidebar,
  Toolbar,
} from "@maykin-ui/admin-ui";
import "@maykin-ui/admin-ui/style";
import "@maykin-ui/admin-ui/style/themes/blue-suede-shoes.css";
import { invariant, ucFirst } from "@maykin-ui/client-common";
import { type MouseEventHandler, useMemo } from "react";
import { Outlet, useNavigate, useNavigation } from "react-router";
import { GlobalSearchButton } from "~/components";
import { useModuleRouteMatch } from "~/hooks/usemodule";
import { apiClient } from "~/lib";
import { logout } from "~/modules/auth";
import { routes } from "~/routes.ts";

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
  const moduleRouteMatch = useModuleRouteMatch();

  // Authenticated root route.
  const authenticatedRootRoute = useMemo(
    () =>
      routes
        .flatMap((r) => [r, ...(r.children || [])])
        .find((r) => r.id === "authenticated-root"),
    [routes],
  );

  invariant(
    authenticatedRootRoute,
    'No authetnicatedRoot root found! Please set `id: "authenticated-root"` on route.',
  );

  // Module root route withing authenticated root route.
  const moduleRootRoute = useMemo(
    () =>
      [authenticatedRootRoute, ...(authenticatedRootRoute.children || [])]
        ?.flatMap((r) => [r, ...(r.children || [])])
        .find((r) => r.handle),
    [authenticatedRootRoute],
  );

  invariant(
    moduleRootRoute,
    "No module root found! Please set `handle: { moduleRoot: true }` on parent route of modules within authenticated-root.",
  );

  // Dynamically created navbar items for modules.
  const moduleNavbarItems = useMemo(
    () =>
      moduleRootRoute.children
        ?.filter((r) => !r.index)
        .map((r) => {
          const path = r.path;
          const icon = r.handle?.icon;

          invariant(path, "Module route must specify path!");
          invariant(icon, "Moduler route must specify icon element on handle!");

          return (
            <Button
              key={path}
              variant="transparent"
              square
              title={ucFirst(path)}
              onClick={() => navigate(`/${path}`)}
            >
              {icon}
            </Button>
          );
        }) || [],
    [moduleRootRoute, navigate],
  );

  const handleLogoClick: MouseEventHandler = (e) => {
    e.preventDefault();
    return navigate("/");
  };

  const handleLogout = async () => {
    await logout();
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

        ...moduleNavbarItems,

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
            // @ts-expect-error - handle is untyped.
            items={moduleRouteMatch.handle?.sidebar?.items}
          />
        </Sidebar>
      }
    >
      <ModalService>
        <ConfigContext.Provider
          value={{
            templatesContentOnly: true,
            templatesGrid: false,
          }}
        >
          <Outlet />
        </ConfigContext.Provider>
      </ModalService>
    </BaseTemplate>
  );
};
