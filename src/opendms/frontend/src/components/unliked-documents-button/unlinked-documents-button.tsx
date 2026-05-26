import { Button, Outline } from "@maykin-ui/admin-ui";
import { NavLink, useMatches, useParams } from "react-router";

export type YearSelectProps = {
  basepath?: string;
};

/**
 * Allows selection of a zaaktype, powered by a loader function.
 * Updates the route to `/:service_slug/:zaaktype_slug` upon selection
 */
export function UnlinkedDocumentsButton({ basepath = "/" }: YearSelectProps) {
  // TODO: Validation. See issue gh-#42
  const { serviceSlug, zaaktypeUuid } = useParams() as {
    serviceSlug: string | undefined;
    zaaktypeUuid: string | undefined;
  };
  const match = [...useMatches()].pop();
  const current = match?.pathname;
  const target = `/${basepath}/${serviceSlug}/documenten-zonder-zaak`;
  const isActive = target === current;

  console.log(zaaktypeUuid);

  return (
    serviceSlug && (
      <NavLink key={"unlinked-documents"} to={target}>
        <Button active={isActive}>
          <Outline.QuestionMarkCircleIcon />
          Toon documenten zonder zaak
        </Button>
      </NavLink>
    )
  );
}
