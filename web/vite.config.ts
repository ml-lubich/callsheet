import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

const DEV_WORK = resolve(__dirname, "../examples/product-review");

/** Locate the directory holding content.json, tolerating a project root or a work dir. */
function workDir(): string {
  const given = process.env.CALLSHEET_WORK || DEV_WORK;
  for (const dir of [given, resolve(given, "work")]) {
    if (existsSync(resolve(dir, "content.json"))) return dir;
  }
  throw new Error(
    `CALLSHEET_WORK: no content.json under ${given} (looked in ${given} and ${given}/work)`,
  );
}

/** The optional inline SVG fragment, beside the data or in the sibling out/ directory. */
function diagrams(work: string): string {
  const project = dirname(work);
  for (const p of [
    resolve(work, "diagrams.html"),
    resolve(work, "../out/diagrams.html"),
    resolve(project, "diagrams.html"),
  ]) {
    if (existsSync(p)) return readFileSync(p, "utf8");
  }
  return "";
}

/** Reads the pipeline's JSON at build time and serves it as one virtual module. */
function callsheetData(): Plugin {
  const id = "virtual:callsheet-data";
  const resolved = "\0" + id;
  return {
    name: "callsheet-data",
    resolveId: (source) => (source === id ? resolved : null),
    load(source) {
      if (source !== resolved) return null;
      const work = workDir();
      const read = (name: string) => readFileSync(resolve(work, name), "utf8");
      this.addWatchFile(resolve(work, "content.json"));
      return [
        `export const CONTENT = ${read("content.json")};`,
        `export const TURNS = ${read("turns.json")};`,
        `export const METRICS = ${read("metrics.json")};`,
        `export const DIAGRAMS = ${JSON.stringify(diagrams(work))};`,
      ].join("\n");
    },
  };
}

export default defineConfig({
  plugins: [react(), callsheetData(), viteSingleFile()],
  build: { assetsInlineLimit: 100_000_000, chunkSizeWarningLimit: 4000 },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
