import { Button, Outline } from "@maykin-ui/admin-ui";
import { NavLink, type RouteObject, useParams } from "react-router";
import { ServiceSelect } from "~/components";
import {
  ZaaktypenList,
  ZakenList,
  zaaktypenListLoader,
  zakenListLoader,
} from "~/modules/zaken/routes/index";
import { ZakenFallback } from "~/modules/zaken/routes/zaken-fallback";

type ZakenNavigationProps = {
  path: string;
};

function ZakenNavigation({ path }: ZakenNavigationProps) {
  const { serviceSlug } = useParams();

  return (
    <>
      <ServiceSelect key="service-select" basepath={path} />
      {serviceSlug && (
        <>
          {/* TODO */}
          <NavLink to={`${path}/${serviceSlug}/zaken`}>
            <Button>Zaken</Button>
          </NavLink>

          <NavLink to={`${path}/${serviceSlug}/zaaktypen`}>
            <Button>Zaaktypen</Button>
          </NavLink>
        </>
      )}
    </>
  );
}

/**
 * Return ths modules routes made available under `path`.
 *
 * @param {string} path - The base path for the routes.
 * @return {RouteObject[]} An array of route objects defining the module's routing structure.
 */
export function createModuleRoutes(path: string): RouteObject[] {
  return [
    {
      path: path,
      handle: {
        icon: <Outline.BookOpenIcon />,
        sidebar: {
          items: [<ZakenNavigation key="navigation" path={path} />],
        },
      },
      children: [
        {
          path: ":serviceSlug?",
          children: [
            {
              path: "zaken",
              loader: zakenListLoader,
              Component: ZakenList,
            },
            {
              path: "zaaktypen",
              loader: zaaktypenListLoader,
              Component: ZaaktypenList,
            },
            {
              index: true,
              Component: ZakenFallback,
            },
          ],
        },
      ],
    },
  ];
}
