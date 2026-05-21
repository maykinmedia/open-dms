import type { RouteObject } from "react-router";

import { zaaktypeLoader } from "./documents-module.loader";
import {
  DocumentsList,
  ZakenList,
  documentsListLoader,
  zakenListLoader,
} from "./routes/index";

export const routes: RouteObject[] = [
  {
    id: "documents-root",
    path: ":serviceSlug?/:zaaktypeUuid?/:zaakYear?",
    loader: zaaktypeLoader,
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
