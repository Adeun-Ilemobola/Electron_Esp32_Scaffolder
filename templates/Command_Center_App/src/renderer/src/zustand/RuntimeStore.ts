import { create } from "zustand";
export type ModuleEntry<
  TPayload extends object = Record<string, any>,
  TModuleType extends string = string
> = {
  id: string;
  moduleType: TModuleType;
  connected: boolean;
  payload: TPayload;
};

type RuntimeStore = {
  modules: Record<string, ModuleEntry>;

  registerModule: (module: ModuleEntry) => void;
  patchModuleState: (id: string, patch: Record<string, any>) => void;
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

  patchModuleState: (id, newPayload) =>
    set((state) => {
      const current = state.modules[id];
      if (!current) return state;

      return {
        modules: {
          ...state.modules,
          [id]: {
            ...current,
            payload: {
              ...current.payload,
              ...newPayload,

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
