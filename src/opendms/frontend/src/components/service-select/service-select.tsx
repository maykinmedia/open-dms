import { type LoadOptionsFn, type Option, Select } from "@maykin-ui/admin-ui";
import { useNavigate, useParams } from "react-router";
import { apiClient } from "~/lib";

/**
 * Allows selection of a service, powered by a loader function.
 * Updates the route to `/:service_slug` upon selection
 */
export function ServiceSelect() {
  const navigate = useNavigate();
  // TODO: Validation. See issue gh-#42
  const { service_slug } = useParams() as { service_slug: string | undefined };

  /**
   * Fetches the service options from the backend (client-side)
   * Accepts string as the first parameter according to `@maykin-ui / LoadOptionsFn` and returns a Promise of results
   * @param search
   */
  const getServiceOptions: LoadOptionsFn = async (
    search,
  ): Promise<Option[]> => {
    const { data } = await apiClient.GET("/api/v1/services", {
      params: {
        query: {
          search,
        },
      },
    });

    return (
      data?.results.map(({ label, slug }) => ({
        label,
        value: slug,
      })) || []
    );
  };

  /**
   * Routes to `:service_slug`
   * @param value
   */
  const setSelectedService = (value: string) => {
    navigate(`/${value}`);
  };

  return (
    <Select
      labelNoOptions="Geen resultaten"
      options={getServiceOptions}
      placeholder="Selecteer service"
      placeholderSearch="Zoeken"
      value={service_slug}
      variant="secondary"
      onChange={({ target }) => setSelectedService(target.value)}
    />
  );
}
