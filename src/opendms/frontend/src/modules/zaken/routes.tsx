import { Button } from "@maykin-ui/admin-ui";
import { NavLink, type RouteObject, useParams } from "react-router";
import { ServiceSelect } from "~/components";
import {
  ZaaktypenList,
  zaaktypenListLoader,
} from "~/modules/zaken/routes/index";

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
          {/*<NavLink to={`${path}/${serviceSlug}/zaken`}>*/}
          {/*  <Button>Zaken</Button>*/}
          {/*</NavLink>*/}

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
              element: "zaken",
            },
            {
              index: true,
              loader: zaaktypenListLoader,
              Component: ZaaktypenList,
            },
          ],
        },
      ],
    },
  ];
}
