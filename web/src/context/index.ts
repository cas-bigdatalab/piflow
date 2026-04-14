import { createContext } from "react";

export const GlobalContext = createContext<{
  userId: string;
}>({
  userId: "",
});
