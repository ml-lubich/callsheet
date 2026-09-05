import type { ComponentType } from "react";

/**
 * Figure overrides. The diagrams fragment is hand-authored SVG keyed by figure id; a
 * project that would rather draw one of those figures in React registers a component
 * under the same id and it takes the fragment figure's place. An id the fragment does
 * not have is appended instead, so this both replaces and extends.
 */
export interface FigureProps {
  id: string;
}

const REGISTRY = new Map<string, ComponentType<FigureProps>>();

export function registerFigure(id: string, component: ComponentType<FigureProps>): void {
  REGISTRY.set(id, component);
}

export function figureFor(id: string): ComponentType<FigureProps> | undefined {
  return REGISTRY.get(id);
}

export function registeredFigureIds(): string[] {
  return [...REGISTRY.keys()];
}

/** Test seam. Nothing in the page calls this. */
export function clearFigures(): void {
  REGISTRY.clear();
}
