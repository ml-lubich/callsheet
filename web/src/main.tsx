import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { DECK } from "./data";
import "./theme.css";
import "./app.css";

document.title = DECK.content.meta?.title || document.title;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App deck={DECK} />
  </StrictMode>,
);
