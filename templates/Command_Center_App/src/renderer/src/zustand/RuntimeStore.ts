import { create } from "zustand";

type ModuleEntry = {
  id: string;
  moduleType: string;
  connected: boolean;
  capabilities: Record<string, unknown>;
  state: Record<string, unknown>;
};

type RuntimeStore = {
  modules: Record<string, ModuleEntry>;

  registerModule: (module: ModuleEntry) => void;
  patchModuleState: (id: string, patch: Record<string, unknown>) => void;
  removeModule: (id: string) => void;
};

export const useRuntimeStore = create<RuntimeStore>((set) => ({
  modules: {},

  registerModule: (module) =>
    set((state) => ({
      modules: {
        ...state.modules,
        [module.id]: module,
      },
    })),

  patchModuleState: (id, patch) =>
    set((state) => {
      const current = state.modules[id];
      if (!current) return state;

      return {
        modules: {
          ...state.modules,
          [id]: {
            ...current,
            state: {
              ...current.state,
              ...patch,
            },
          },
        },
      };
    }),

  removeModule: (id) =>
    set((state) => {
      const next = { ...state.modules };
      delete next[id];
      return { modules: next };
    }),
}));