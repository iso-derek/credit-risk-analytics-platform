import { createContext, useContext, useState, type ReactNode } from "react";
import { apiUrl, useApi, type Dataset, type Meta } from "./api";
import { setCurrency } from "./format";

interface DatasetState {
  dataset: Dataset;
  setDataset: (dataset: Dataset) => void;
  meta: Meta | undefined;
  metaError: string | undefined;
}

const DatasetContext = createContext<DatasetState | null>(null);

function initialDataset(): Dataset {
  try {
    return localStorage.getItem("credit-dataset") === "uci" ? "uci" : "synthetic";
  } catch {
    return "synthetic";
  }
}

export function DatasetProvider({ children }: { children: ReactNode }) {
  const [dataset, setDatasetState] = useState<Dataset>(initialDataset);
  const { data: meta, error: metaError } = useApi<Meta>(apiUrl("meta", dataset));
  const setDataset = (next: Dataset) => {
    setDatasetState(next);
    try {
      localStorage.setItem("credit-dataset", next);
    } catch {
      /* storage unavailable: keep in memory only */
    }
  };
  // Hold rendering of pages until the currency for this dataset is known.
  const ready = meta && meta.dataset === dataset ? meta : undefined;
  if (ready) setCurrency(ready.currency); // set before children format any money
  return <DatasetContext.Provider value={{ dataset, setDataset, meta: ready, metaError }}>{children}</DatasetContext.Provider>;
}

export function useDataset(): DatasetState {
  const value = useContext(DatasetContext);
  if (!value) throw new Error("useDataset must be used inside DatasetProvider");
  return value;
}
