import {
  Body,
  type FieldSet,
  Form,
  KanbanTemplate,
  Modal,
  P,
  Textarea,
  useAlert,
} from "@maykin-ui/admin-ui";
import { useState } from "react";
import { useLoaderData, useParams, useRevalidator } from "react-router";
import { apiClient, getCSRFToken } from "~/lib";
import type { StatusType } from "~/types";

import type {
  ZaakWithStatus,
  zaaktypeDetailLoader,
} from "./zaaktype-detail.loader";

type PendingChange = {
  zaak: ZaakWithStatus;
  sourceColIndex: number;
  targetColIndex: number;
  targetStatustype: StatusType;
};

function buildKanbanData(
  statustypen: StatusType[],
  zaken: ZaakWithStatus[],
): { fieldsets: FieldSet<ZaakWithStatus>[]; objectLists: ZaakWithStatus[][] } {
  const fieldsets: FieldSet<ZaakWithStatus>[] = [
    [
      "Geen status",
      {
        fields: ["identificatie", "omschrijving"],
        title: "identificatie",
      },
    ],
    ...statustypen.map(
      (statustype): FieldSet<ZaakWithStatus> => [
        statustype.omschrijving,
        {
          fields: ["identificatie", "omschrijving"],
          title: "identificatie",
        },
      ],
    ),
  ];

  const objectLists: ZaakWithStatus[][] = [
    zaken.filter((zaak) => !zaak.statustype),
    ...statustypen.map((statustype) => zaken.filter((zaak) => zaak.statustype === statustype.url)),
  ];

  return { fieldsets, objectLists };
}

export function ZaaktypeDetail() {
  const { serviceSlug, zaaktypeUuid } = useParams() as {
    serviceSlug: string;
    zaaktypeUuid: string;
  };
  const data = useLoaderData<typeof zaaktypeDetailLoader>();
  const revalidator = useRevalidator();
  const alert = useAlert();

  const [kanbanKey, setKanbanKey] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [nieuweZaakOpen, setNieuweZaakOpen] = useState(false);
  const [creatingZaak, setCreatingZaak] = useState(false);
  const [pendingChange, setPendingChange] = useState<PendingChange | null>(
    null,
  );
  const [toelichting, setToelichting] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { zaaktype, statustypen, zaken } = data;

  const anyZaak = zaken[0] ?? null;

  const filteredZaken = searchQuery
    ? zaken.filter(
        (zaak) =>
          zaak.identificatie.toLowerCase().includes(searchQuery.toLowerCase()) ||
          zaak.omschrijving.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : zaken;

  const { fieldsets, objectLists } = buildKanbanData(
    statustypen,
    filteredZaken,
  );

  const title = zaaktype.omschrijving || zaaktype.identificatie;

  const applyStatusChange = async (
    zaak: ZaakWithStatus,
    targetStatustype: StatusType,
    statustoelichting?: string,
  ) => {
    try {
      const response = await fetch(
        `/api/v1/services/${serviceSlug}/zaaktypen/${zaaktypeUuid}/zaken/${zaak.uuid}/statussen`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify({
            zaak: zaak.url,
            statustype: targetStatustype.url,
            datumStatusGezet: new Date().toISOString(),
            ...(statustoelichting ? { statustoelichting } : {}),
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Status wijzigen mislukt: ${response.statusText}`);
      }
    } catch (err) {
      alert(
        "Fout",
        err instanceof Error ? err.message : "Status wijzigen mislukt",
        "Ok",
      );
      setKanbanKey((key) => key + 1);
    } finally {
      revalidator.revalidate();
    }
  };

  const handleObjectChange = (
    zaak: ZaakWithStatus,
    srcColIndex: number,
    tgtColIndex: number,
  ) => {
    if (tgtColIndex === 0) {
      setKanbanKey((key) => key + 1);
      return;
    }

    const targetStatustype = statustypen[tgtColIndex - 1];

    if (!targetStatustype) {
      setKanbanKey((key) => key + 1);
      return;
    }

    const needsModal =
      (targetStatustype.checklistitemStatustype?.length ?? 0) > 0 ||
      targetStatustype.isEindstatus;

    if (needsModal) {
      setPendingChange({
        zaak,
        sourceColIndex: srcColIndex,
        targetColIndex: tgtColIndex,
        targetStatustype,
      });
      return;
    }

    applyStatusChange(zaak, targetStatustype);
  };

  const handleConfirm = async () => {
    if (!pendingChange) return;
    setSubmitting(true);
    try {
      await applyStatusChange(
        pendingChange.zaak,
        pendingChange.targetStatustype,
        toelichting || undefined,
      );
    } finally {
      setSubmitting(false);
      setPendingChange(null);
      setToelichting("");
    }
  };

  const handleCancel = () => {
    setPendingChange(null);
    setToelichting("");
    setKanbanKey((key) => key + 1);
  };

  const handleNieuweZaak = async (
    _: React.FormEvent<HTMLFormElement>,
    formData: Record<string, string>,
  ) => {
    setCreatingZaak(true);
    try {
      const { data: newZaak, response } = await apiClient.POST(
        "/api/v1/services/{serviceSlug}/zaken",
        {
          params: { path: { serviceSlug } },
          body: {
            zaaktype: zaaktype.url,
            startdatum: formData.startdatum,
            bronorganisatie: formData.bronorganisatie,
            verantwoordelijkeOrganisatie: formData.verantwoordelijkeOrganisatie,
            ...(formData.omschrijving
              ? { omschrijving: formData.omschrijving }
              : {}),
          },
        },
      );

      if (!response.ok || !newZaak) {
        throw new Error("Aanmaken zaak mislukt");
      }

      setNieuweZaakOpen(false);
      revalidator.revalidate();
    } catch (err) {
      alert(
        "Fout",
        err instanceof Error ? err.message : "Aanmaken zaak mislukt",
        "Ok",
      );
    } finally {
      setCreatingZaak(false);
    }
  };

  const modalTitle = pendingChange?.targetStatustype.isEindstatus
    ? "Zaak afronden"
    : "Status wijzigen";

  const checklistItems =
    pendingChange?.targetStatustype.checklistitemStatustype ?? [];

  return (
    <>
      <KanbanTemplate<ZaakWithStatus>
        key={kanbanKey}
        breadcrumbItems={[
          { label: "Zaaktypen", href: ".." },
          { label: title, href: "." },
        ]}
        kanbanProps={{
          title,
          toolbarProps: {
            align: "end",
            overrideItemProps: false,
            items: [
              {
                type: "text",
                placeholder: "Zoeken…",
                size: "s",
                value: searchQuery,
                onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                  setSearchQuery(e.target.value),
              },
              {
                componentType: "button",
                children: "+ Nieuwe zaak",
                variant: "primary",
                onClick: () => setNieuweZaakOpen(true),
              },
            ],
          },
          fieldsets,
          objectLists,
          draggable: true,
          onObjectChange: handleObjectChange,
        }}
      />
      <Modal
        open={pendingChange !== null}
        onClose={handleCancel}
        title={modalTitle}
        size="s"
        actions={[
          {
            children: submitting ? "Bezig…" : "Bevestigen",
            variant: "primary",
            onClick: handleConfirm,
            disabled: submitting,
          },
          {
            children: "Annuleren",
            onClick: handleCancel,
            disabled: submitting,
          },
        ]}
      >
        {pendingChange && (
          <Body>
            <P>
              Zaak <strong>{pendingChange.zaak.identificatie}</strong>{" "}
              verplaatsen naar{" "}
              <strong>{pendingChange.targetStatustype.omschrijving}</strong>.
            </P>

            {checklistItems.length > 0 && (
              <ul>
                {checklistItems.map((item) => (
                  <li key={item.itemnaam}>{item.itemnaam}</li>
                ))}
              </ul>
            )}

            <Textarea
              label="Toelichting (optioneel)"
              value={toelichting}
              onChange={(e) =>
                setToelichting(
                  (e as React.ChangeEvent<HTMLTextAreaElement>).target.value,
                )
              }
              size="xl"
            />
          </Body>
        )}
      </Modal>
      <Modal
        open={nieuweZaakOpen}
        onClose={() => setNieuweZaakOpen(false)}
        title="Nieuwe zaak"
        size="m"
      >
        <Form
          fields={[
            {
              label: "Omschrijving",
              name: "omschrijving",
              type: "text",
              required: false,
            },
            {
              label: "Startdatum",
              name: "startdatum",
              type: "date",
              required: true,
            },
            {
              label: "Bronorganisatie",
              name: "bronorganisatie",
              type: "text",
              required: true,
            },
            {
              label: "Verantwoordelijke organisatie",
              name: "verantwoordelijkeOrganisatie",
              type: "text",
              required: true,
            },
          ]}
          initialValues={{
            startdatum: new Date().toISOString().split("T")[0],
            bronorganisatie: anyZaak?.bronorganisatie ?? "",
            verantwoordelijkeOrganisatie:
              anyZaak?.verantwoordelijkeOrganisatie ?? "",
          }}
          labelSubmit={creatingZaak ? "Bezig…" : "Aanmaken"}
          onSubmit={handleNieuweZaak}
        />
      </Modal>
    </>
  );
}
