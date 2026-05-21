import type { RouteObject } from "react-router";

import {
  DocumentsList,
  ZakenList,
  documentsListLoader,
  zakenListLoader,
} from "./routes/index";

export const routes: RouteObject[] = [
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
];
