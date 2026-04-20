import {
  Button,
  GlobalSearch,
  Modal,
  Outline,
  type SearchResult,
} from "@maykin-ui/admin-ui";
import { useState } from "react";
import { useNavigate } from "react-router";

export type { SearchResult };

export type GlobalSearchButtonProps = {
  search: (
    query: string,
    options: { signal: AbortSignal },
  ) => Promise<SearchResult[]>;
};

export const GlobalSearchButton = ({ search }: GlobalSearchButtonProps) => {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleNavigate = (href: string) => {
    setOpen(false);
    navigate(href);
  };

  return (
    <>
      <Button
        aria-label="Zoek overal"
        square
        variant="transparent"
        onClick={() => setOpen(true)}
      >
        <Outline.MagnifyingGlassIcon />
      </Button>
      {/*// TODO: I think a bigger modal would be better*/}
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        showClose={false}
        size="m"
      >
        <GlobalSearch
          search={search}
          onClose={() => setOpen(false)}
          onNavigate={handleNavigate}
        />
      </Modal>
    </>
  );
};
