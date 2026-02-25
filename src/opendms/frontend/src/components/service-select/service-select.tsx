import { type Option, Select } from "@maykin-ui/admin-ui";
import { type FC } from "react";
import { useSearchParams } from "react-router";

const SEARCH_PARAM_NAME = "service-select";

interface ServiceSelectProps {
  options: Option[];
}
export const ServiceSelect: FC<ServiceSelectProps> = ({ options = [] }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const selectedService = searchParams.get(SEARCH_PARAM_NAME);

  const setSelectedService = (value: string) => {
    setSearchParams((searchParams) => {
      searchParams.set(SEARCH_PARAM_NAME, value);
      return searchParams;
    });
  };

  return (
    <Select
      options={options}
      placeholder="Selceteer Service"
      value={selectedService}
      variant="secondary"
      onChange={({ target }) => setSelectedService(target.value)}
    />
  );
};
