import {
  type ItemGridButtonProps,
  type ItemGridItemProps,
  ItemGridTemplate,
  Outline,
  P,
  useAlert,
  useConfirm,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import { useCallback, useEffect, useMemo, useState } from "react";
import * as React from "react";
import {
  useLoaderData,
  useParams,
  useRevalidator,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import { usePoll } from "~/hooks";
import { getPageFromSearchParams } from "~/lib";
import { authenticatedRootLoader } from "~/routes/authenticated-root.loader.ts";
import {
  type documentsListLoader,
  fetchDocuments,
} from "~/routes/documents-list/documents-list.loader.ts";
import type { Document } from "~/types";

export const DocumentsList = () => {
  // TODO: Validation. See issue gh-#42
  const data = useLoaderData<typeof documentsListLoader>();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = searchParams.get("page") || undefined;

  // Active windows for editing.
  const [activeEditorWindowsState, setActiveEditorWindowsState] =
    useState<Record<string, Window>>();

  // Document uuid's that are being uploaded.
  const [pendingDocumentUuidsState, setPendingDocumentUuidsState] = useState<
    string[]
  >([]);

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
  const confirm = useConfirm();
  const { revalidate } = useRevalidator();
  const highlight = searchParams.get("highlight");

  /**
   * Polls the backend for the documents list.
   * Revalidates (reload) the page if anything is changed.
   */
  usePoll(
    async (signal?: AbortSignal) => {
      // Remove closed editors from state.
      const windowEntries = Object.entries(activeEditorWindowsState || {});
      const openWindowEntries = windowEntries.filter(
        ([, window]) => !window.closed,
      );
      if (openWindowEntries.length !== windowEntries.length) {
        setActiveEditorWindowsState(Object.fromEntries(openWindowEntries));
      }

      // Poll for changed documents (revalidate if found).
      if (!serviceSlug || !zaaktypeUuid || !zaakId) return null;

      const { data: pollData, response } = await fetchDocuments(
        serviceSlug,
        zaaktypeUuid,
        zaakId,
        page,
        signal,
      );

      // Revalidate if data is changed.
      if (response.ok) {
        const a = JSON.stringify(data?.results);
        const b = JSON.stringify(pollData?.results);
        if (a !== b) revalidate();
      }
    },
    [
      serviceSlug,
      zaaktypeUuid,
      zaakId,
      activeEditorWindowsState,
      fetchDocuments,
      page,
      data?.results,
    ],
  );

  useEffect(() => {
    if (!highlight || !data) return;
    document
      .getElementById(`${highlight}-info`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight, data]);

  const handleEdit = useCallback(
    async (document: Document, e: React.MouseEvent) => {
      e.preventDefault();
      const path = `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${document.uuid}/edit?originUrl=${window.location}`;
      const response = await fetch(path, { redirect: "manual" });

      const text = await response.text();
      let url;
      let popup;

      // Response should contain the editor URL as a body.
      // Due to implementation-specific CORS restrictions, we can't reply with a `HttpResponseRedirect` and the target
      // location is set on the body.
      if (response.status !== 423) {
        try {
          url = new URL(text);
        } catch {
          alert(
            "Foutmelding!",
            "Fout bij het ophalen van de bewerken-url.",
            "Ok",
          );
          return;
        }
      }

      switch (response.status) {
        // Our `response` indicates an authentication failure.
        // Use `url.href` to redirect the user through an authentication flow.
        // This should return the user to the starting point, allowing documents
        // to be edited.
        case 403:
          invariant(url);
          // TODO: Add notification about renewed document backend session.
          window.location.href = url.href;
          break;

        // Our `response` indicates that the resource is blocked.
        case 423:
          alert(
            "Foutmelding!",
            "Document geblokkeerd. Probeer later opnieuw.",
            "Ok",
          );
          break;

        // Our `response` indicates an authenticated response.
        // Open `url.href` and check if `popup` is closed befor allowing saves.
        // Note: this is not a fail-save check and only works a long as the
        // frontend is not reloaded and the browser keeps track of the `popup`
        // `Window` object.
        default:
          invariant(url);
          popup = window.open(url.href);
          if (!popup) return;

          setActiveEditorWindowsState({
            ...activeEditorWindowsState,
            [document.uuid]: popup,
          });

          alert(
            "Waarschuwing!",
            "Sluit altijd eerst de bewerken omgeving voordat u wijzigen opslaat.",
            "Ok",
          );
      }
    },
    [serviceSlug, zaaktypeUuid, zaakId, alert, activeEditorWindowsState],
  );

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
   * @param {Document} document
   * @param {MouseEvent} e - The mouse event triggered by the user interaction.
   */
  const handleUpload = useCallback(
    (document: Document, e: React.MouseEvent) => {
      e.preventDefault();
      const target: HTMLAnchorElement = e.target as HTMLAnchorElement;

      const _onConfirm = () => {
        setPendingDocumentUuidsState([
          ...pendingDocumentUuidsState,
          document.uuid,
        ]);
        return fetch(target.href)
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
              revalidate,
            ),
          )
          .catch(() =>
            alert("Foutmelding!", "Document kon niet worden opgeslagen.", "Ok"),
          )
          .finally(() => {
            setPendingDocumentUuidsState(
              pendingDocumentUuidsState.filter(
                (uuid) => uuid !== document.uuid,
              ),
            );
            revalidate();
          });
      };

      confirm(
        "Waarschuwing!",
        'Sluit altijd eerst de bewerken omgeving en klik dan op "Opslaan"',
        "Opslaan",
        "Annuleren",
        _onConfirm,
      );
    },
    [pendingDocumentUuidsState, confirm, alert, revalidate],
  );

  const ACTION_DOWNLOAD = (document: Document): ItemGridButtonProps => ({
    as: "a",
    children: <Outline.ArrowDownOnSquareIcon />,
    download: true,
    href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${document.uuid}/download`,
    title: "Bestand downloaden",
  });

  const ACTION_EDIT = (document: Document): ItemGridButtonProps => ({
    as: "a",
    children: <Outline.PencilSquareIcon />,
    href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${document.uuid}/edit`,
    title: "Bestand bewerken",
    target: "_blank",
    onClick: (e: React.MouseEvent) => handleEdit(document, e),
  });

  const ACTION_UPLOAD = (doc: Document): ItemGridButtonProps => {
    const isEditing =
      activeEditorWindowsState !== undefined &&
      activeEditorWindowsState[doc.uuid] !== undefined &&
      activeEditorWindowsState[doc.uuid].closed === false;

    const title = isEditing
      ? 'Sluit altijd eerst de bewerken omgeving en klik dan op "Opslaan"'
      : "Bestand opslaan in Open Zaak.";

    return {
      as: "a",
      children: (
        <>
          {pendingDocumentUuidsState.includes(doc.uuid) ? (
            <Outline.ArrowPathIcon spin />
          ) : (
            <Outline.CloudArrowUpIcon />
          )}
          Opslaan
        </>
      ),
      disabled: isEditing || pendingDocumentUuidsState.includes(doc.uuid),
      href: `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaakId}/documents/${doc.uuid}/upload`,
      square: false,
      target: "_blank",
      title,
      onClick: (e: React.MouseEvent) => handleUpload(doc, e),
    };
  };

  const items = useMemo<ItemGridItemProps[]>(
    () =>
      data?.results?.map((doc) => {
        const isEditing =
          activeEditorWindowsState !== undefined &&
          activeEditorWindowsState[doc.uuid] !== undefined &&
          activeEditorWindowsState[doc.uuid].closed === false;

        return {
          id: doc.uuid,
          highlighted: doc.uuid === highlight,
          title: doc.titel,
          icon: <Outline.DocumentIcon />,
          informationLines: [
            doc.identificatie,
            isEditing ? "Bezig met bewerken…" : false,
          ].filter(Boolean),
          actions: doc.hasPendingUpdates
            ? [ACTION_DOWNLOAD(doc), ACTION_EDIT(doc), ACTION_UPLOAD(doc)]
            : [ACTION_DOWNLOAD(doc), ACTION_EDIT(doc)],
        };
      }) ?? [],
    [
      activeEditorWindowsState,
      data?.results,
      highlight,
      ACTION_DOWNLOAD,
      ACTION_EDIT,
      ACTION_UPLOAD,
    ],
  );

  if (!data) return null;
  invariant(rootData?.zaaktype?.identificatie, "Zaaktype not loaded!");

  return (
    <ItemGridTemplate
      title={`${rootData.zaaktype.identificatie} / ${zaakYear} / ${data.zaak.identificatie}`}
      itemGridProps={{ direction: "v", ellipsis: true, items }}
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
