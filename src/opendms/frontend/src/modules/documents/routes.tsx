import type { RouteObject } from "react-router";
import { ServiceSelect, YearSelect, ZaaktypeSelect } from "~/components";

import {
  DocumentsList,
  ZakenList,
  documentsListLoader,
  zakenListLoader,
} from "./routes/index";

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
          items: [
            <ServiceSelect key="service-select" basepath={path} />,
            <ZaaktypeSelect key="zaaktype-select" basepath={path} />,
            <YearSelect key="year-select" basepath={path} />,
          ],
        },
      },
      children: [
        {
          path: ":serviceSlug?/:zaaktypeUuid?/:zaakYear?",
          children: [
            {
              index: true,
              Component: ZakenList,
              loader: zakenListLoader,
            },
            {
              path: ":zaakId",
              Component: DocumentsList,
              loader: documentsListLoader,
            },
          ],
        },
      ],
    },
  ];
}
