import {
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
  P,
  useAlert,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { type MouseEventHandler, useCallback, useMemo } from "react";
import {
  useLoaderData,
  useParams,
  useRevalidator,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import { getPageFromSearchParams } from "~/lib";
import { authenticatedRootLoader } from "~/routes/authenticated-root.loader.ts";
import type { documentsListLoader } from "~/routes/documents-list/documents-list.loader.ts";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();
  const [searchParams, setSearchParams] = useSearchParams();

  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid, zaakYear, zaakId } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
    zaakYear: string | undefined;
    zaakId: string | undefined;
  };
  const rootData =
    useRouteLoaderData<typeof authenticatedRootLoader>("authenticated-root");

  const alert = useAlert();
  const { revalidate } = useRevalidator();

  /**
   * Handles the upload of a document by fetching the resource from the provided link
   * (anchor element's href) and processing the response. If the fetch operation
   * is successful, it displays a success alert; otherwise, it shows an error alert.
   * The function ensures that an optional revalidation action is triggered in the end.
   *
   * Dependencies:
   * - Uses the `useCallback` hook for memoizing the function instance.
   * - Uses an `alert` function to display user feedback messages.
   * - Calls a `revalidate` function after the operation completes, regardless of success.
   *
   * @param {MouseEvent} e - The mouse event triggered by the user interaction.
   */
  const handleUpload = useCallback<MouseEventHandler<Element>>(
    (e) => {
      e.preventDefault();
      const target: HTMLAnchorElement = e.target as HTMLAnchorElement;
      fetch(target.href)
        .then((response: Response) => {
          if (!response.ok) throw response;
          return response;
        })
        .then((response) => response.json())
        .then(() =>
          alert(
            "Document opgeslagen",
            "Document is successvol opgeslagen in Open Zaak.",
            "Ok",
          ),
        )
        .catch(() =>
          alert("Foutmelding!", "Document kon niet worden opgeslagen.", "Ok"),
        )
        .finally(revalidate);
    },
    [alert, revalidate],
  );

  const items = useMemo<ItemGridItemProps[]>(() => {
    return (
      data?.results.map((doc) => {
        return {
          title: doc.titel,
          icon: <Outline.DocumentIcon />,
          informationLines: [doc.formaat],
          actions: doc.hasPendingUpdates
            ? [
                {
                  as: "a",
                  children: <Outline.ArrowDownOnSquareIcon />,
                  download: true,
                  href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/download`,
                  title: "Bestand downloaden",
                },
                {
                  as: "a",
                  children: <Outline.PencilSquareIcon />,
                  href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/edit`,
                  title: "Bestand bewerken",
                  target: "_blank",
                },
                {
                  as: "a",
                  children: (
                    <>
                      <Outline.CloudArrowUpIcon />
                      Opslaan
                    </>
                  ),
                  href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/upload`,
                  square: false,
                  target: "_blank",
                  title: "Bestand opslaan in Open Zaak",
                  onClick: handleUpload,
                },
              ]
            : [
                {
                  as: "a",
                  children: <Outline.ArrowDownOnSquareIcon />,
                  download: true,
                  href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/download`,
                  title: "Bestand downloaden",
                },
                {
                  as: "a",
                  children: (
                    <>
                      <Outline.PencilSquareIcon />
                      Bewerken
                    </>
                  ),
                  href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/edit`,
                  square: false,
                  title: "Bestand bewerken",
                  target: "_blank",
                },
              ],
        };
      }) ?? []
    );
  }, [data?.results, serviceSlug, zaaktypeUuid, zaakId, handleUpload]);

  if (!data) return null;
  invariant(rootData?.zaaktype?.identificatie, "Zaaktype not loaded!");

  return (
    <ItemGridTemplate
      title={`${rootData.zaaktype.identificatie} / ${zaakYear} / documenten`}
      itemGridProps={{ ellipsis: true, items }}
      paginatorProps={{
        count: data.count,
        page: getPageFromSearchParams(searchParams),
        pageSize: 20,
        onPageChange: (page) => setSearchParams({ page: page.toString() }),
      }}
    >
      <P>{data.count} documenten</P>
    </ItemGridTemplate>
  );
};
