import {
  A,
  ListTemplate,
  Outline,
  type TypedField,
  useAlert,
  useFormDialog,
} from "@maykin-ui/admin-ui";
import { invariant } from "@maykin-ui/client-common";
import type { JSX } from "react";
import {
  useLoaderData,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
import { apiClient, getPageFromSearchParams } from "~/lib";
import type { Zaak } from "~/types";

import type { zakenListLoader } from "./zaken-list.loader";

type CreateZaakFormData = {
  omschrijving: string;
  startdatum: string;
};

export function ZakenList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const { serviceSlug, zaaktypeUuid } = useParams() as {
    serviceSlug: string;
    zaaktypeUuid: string;
  };

  const data = useLoaderData<typeof zakenListLoader>();
  invariant(data, "Zaken data not loaded!");

  const alert = useAlert();
  const formDialog = useFormDialog<CreateZaakFormData>();

  const handleCreateZaak = () => {
    formDialog(
      "Zaak aanmaken",
      null,
      [
        {
          name: "omschrijving",
          label: "Omschrijving",
          type: "text",
          required: true,
        },
        {
          name: "startdatum",
          label: "Startdatum",
          type: "date",
          required: true,
        },
      ],
      "Aanmaken",
      "Annuleren",
      async (formData) => {
        const { data: newZaak, error } = (await apiClient.POST(
          // @ts-expect-error - API not ready
          "/api/v1/services/{serviceSlug}/zaaktypen/{zaaktypenZaaktypeUuid}/zaken",
          {
            params: {
              path: {
                serviceSlug,
                zaaktypenZaaktypeUuid: zaaktypeUuid,
              },
            },
            body: {
              omschrijving: formData.omschrijving,
              startdatum: formData.startdatum,
            },
          },
        )) as unknown as { data: Zaak | undefined; error: unknown };

        if (error || !newZaak) {
          await alert(
            "Foutmelding!",
            "Zaak kon niet worden aangemaakt.",
            "Ok",
          );
          return;
        }

        navigate(newZaak.uuid);
      },
    );
  };

  const fields: TypedField<
    Omit<Zaak, "identificatie"> & { identificatie: JSX.Element }
  >[] = [
    {
      name: "identificatie",
      type: "jsx",
      filterLookup: "identificatie__icontains",
      filterValue: searchParams.get("identificatie__icontains") ?? "",
    },
    {
      name: "omschrijving",
      type: "string",
      filterLookup: "omschrijving",
      filterValue: searchParams.get("omschrijving") ?? "",
    },
    { name: "startdatum", type: "date" },
  ];

  const objectList = data.results.map((zaak) => ({
    ...zaak,
    identificatie: (
      <A
        href={zaak.uuid}
        onClick={(e) => {
          e.preventDefault();
          navigate(zaak.uuid);
        }}
      >
        {zaak.identificatie}
      </A>
    ),
  }));

  return (
    <ListTemplate
      dataGridProps={{
        title: `${serviceSlug} / ${zaaktypeUuid}`,
        objectList: objectList,
        fields: fields,
        filterable: true,
        urlFields: [""],
        paginatorProps: {
          count: data.count,
          page: getPageFromSearchParams(searchParams),
          pageSize: 100,
        },
        onPageChange: (page) => setSearchParams({ page: page.toString() }),
        onFilter: (filterData: Record<string, string>) => {
          searchParams.delete("page");
          setSearchParams({
            ...Object.fromEntries(searchParams),
            ...filterData,
          });
        },
        toolbarItems: [
          "spacer",
          {
            componentType: "button",
            children: (
              <>
                <Outline.PlusIcon />
                Zaak aanmaken
              </>
            ),
            variant: "primary",
            onClick: handleCreateZaak,
          },
        ],
      }}
    />
  );
}
