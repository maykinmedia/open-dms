import { type LoadOptionsFn, Select } from "@maykin-ui/admin-ui";
import { useNavigate, useParams } from "react-router";

type ServiceSelectProps = {
  options: LoadOptionsFn;
};

/**
 * Allows selection of a service, powered by a loader function.
 * Updates the route to `/:service_slug` upon selection
 * @param options
 */
export function ServiceSelect({ options }: ServiceSelectProps) {
  const navigate = useNavigate();

  // TODO: Validation. See issue gh-#42
  const { service_slug } = useParams() as { service_slug: string | undefined };

  /**
   * Routes to `:service_slug`
   * @param value
   */
  const setSelectedService = (value: string) => {
    navigate(`/${value}`);
  };

  return (
    <Select
      options={options}
      placeholder="Selceteer Service"
      placeholderSearch="Zoeken"
      labelNoOptions="Geen resultaten"
      value={service_slug}
      variant="secondary"
      onChange={({ target }) => setSelectedService(target.value)}
    />
  );
}
