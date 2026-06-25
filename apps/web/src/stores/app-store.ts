import { create } from "zustand";
import { persist } from "zustand/middleware";

type AppState = {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  unreadNotifications: number;
  setUnreadNotifications: (count: number) => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      unreadNotifications: 0,
      setUnreadNotifications: (count) => set({ unreadNotifications: count }),
    }),
    { name: "gradpilot-app", partialize: (s) => ({ sidebarCollapsed: s.sidebarCollapsed }) },
  ),
);
