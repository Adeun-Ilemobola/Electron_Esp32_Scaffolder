import { create } from "zustand";
import type { CommandName } from "./Command";
import type { ModulePayloadSchema, RegisteredModuleType } from "./Module";


export type ModuleEntry<
  TModuleType extends RegisteredModuleType = RegisteredModuleType
> = {
  id: string;
  moduleType: TModuleType;
  connected: boolean;
  payload: ModulePayloadSchema[TModuleType];
};

type RuntimeStore = {
  modules: Record<string, ModuleEntry>;

  registerModule: (module: ModuleEntry) => void;
  patchModuleState: (id: string, patch: Record<string, any>) => void;
  removeModule: (id: string) => void;
  clearModules: () => void;
};
export const useRuntimeStore = create<RuntimeStore>((set) => ({
  modules: {},
  clearModules: () => set({ modules: {} }),

  registerModule: (module) =>{
    set((state) => ({
      modules: {
        ...state.modules,
        [module.id]: module,
      },
    }))
  },
    

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
