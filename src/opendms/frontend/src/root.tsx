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
import { Outlet, useNavigate, useNavigation, useParams } from "react-router";
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
type ESZaakRef = {
  uuid: string;
  zaaktype: string;
  startdatum: string;
};

type ESDocResult = {
  titel: string;
  bestandsnaam: string | null;
  zaakReferenties: ESZaakRef[];
};

type ESZaakResult = {
  uuid: string;
  zaaktype: string;
  startdatum: string;
  omschrijving: string;
  serviceSlug: string | null;
};

type SearchResultItem =
  | { type: "document"; data: ESDocResult }
  | { type: "zaak"; data: ESZaakResult };

export const AuthenticatedLayout = () => {
  const navigate = useNavigate();
  const { state } = useNavigation();
  const { serviceSlug } = useParams();

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
    // The OpenAPI schema incorrectly declares the response as Document[] but
    // the API actually returns a paginated response with typed results (document | zaak)
    // TODO: ask backend to fix @extend_schema on SearchView to use inline_serializer
    // wrapping DocumentSerializer(many=True) in a paginated shape
    const results =
      (data as unknown as { results: SearchResultItem[] })?.results ?? [];
    return results.flatMap((item) => {
      if (item.type === "zaak") {
        const { uuid, zaaktype, startdatum, omschrijving, serviceSlug } =
          item.data;
        if (!serviceSlug) return [];
        const zaaktypeUuid = zaaktype.split("/").pop();
        const zaakYear = new Date(startdatum).getFullYear();
        return [
          {
            title: omschrijving,
            href: `/${serviceSlug}/${zaaktypeUuid}/${zaakYear}/${uuid}`,
            icon: <Outline.FolderIcon />,
            group: "Zaken",
          },
        ];
      }

      const zaak = item.data.zaakReferenties?.[0];
      if (!zaak || !serviceSlug) return [];
      const zaaktypeUuid = zaak.zaaktype.split("/").pop();
      const zaakYear = new Date(zaak.startdatum).getFullYear();
      return [
        {
          title: item.data.titel,
          href: `/${serviceSlug}/${zaaktypeUuid}/${zaakYear}/${zaak.uuid}`,
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
        <Logo abbreviated key={"logo"} />,
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
