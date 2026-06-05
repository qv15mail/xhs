import { create } from "zustand";

interface AppState {
  loggedIn: boolean;
  disclaimerAccepted: boolean;
  setLoggedIn: (v: boolean) => void;
  acceptDisclaimer: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  loggedIn: false,
  disclaimerAccepted: localStorage.getItem("redscope.disclaimer") === "1",
  setLoggedIn: (v) => set({ loggedIn: v }),
  acceptDisclaimer: () => {
    localStorage.setItem("redscope.disclaimer", "1");
    set({ disclaimerAccepted: true });
  },
}));
