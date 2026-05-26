import { type RouteObject } from "react-router";
import { ServiceSelect, YearSelect, ZaaktypeSelect } from "~/components";
import { UnlinkedDocumentsButton } from "~/components/unliked-documents-button";

import {
  DocumentsList,
  ZakenList,
  documentsListLoader,
  unlinkedDocumentsListLoader,
  zakenListLoader,
} from "./routes/index";

export const ID_UNLINKED_DOCUMENTS = "unlinked-documents";

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
            <UnlinkedDocumentsButton
              key="unlinked-documents-button"
              basepath={path}
            />,
            <YearSelect key="year-select" basepath={path} />,
          ],
        },
      },
      children: [
        {
          id: ID_UNLINKED_DOCUMENTS,
          path: ":serviceSlug?/documenten-zonder-zaak",
          Component: DocumentsList,
          loader: unlinkedDocumentsListLoader,
        },
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
