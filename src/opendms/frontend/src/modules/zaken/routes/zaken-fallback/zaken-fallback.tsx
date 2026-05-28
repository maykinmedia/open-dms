import { BaseTemplate, Body, P } from "@maykin-ui/admin-ui";

/**
 * Renders the ZakenFallback UI component which provides a fallback view.
 * The component uses a grid layout to center its content vertically and horizontally.
 * It includes a message prompting the user to select a service and the desired overview.
 *
 * @return {JSX.Element} The rendered ZakenFallback component.
 */
export function ZakenFallback() {
  return (
    <BaseTemplate
      grid
      gridProps={{ valign: "middle" }}
      columnProps={{ justify: "center" }}
    >
      <Body>
        <P muted>Selecteer service en het gewenste overzicht.</P>
      </Body>
    </BaseTemplate>
  );
}
