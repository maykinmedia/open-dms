import {
  Button,
  GlobalSearch,
  Modal,
  Outline,
  type SearchResult,
  useKeyboardShortcut,
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

  useKeyboardShortcut({ key: "K", ctrlOrMeta: true }, () =>
    setOpen((open) => !open),
  );

  const handleNavigate = (href: string) => {
    setOpen(false);
    navigate(href);
  };

  return (
    <>
      <Button
        aria-label="Zoeken"
        title="Zoeken (⌘K)"
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
