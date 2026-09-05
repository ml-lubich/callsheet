import { Reveal } from "../components/Reveal";
import { SkeletonLines } from "../components/Skeleton";

export function AbstractSkeleton() {
  return <SkeletonLines n={4} w="66ch" />;
}

export function Abstract({ text }: { text: string }) {
  // The writer splits the abstract into paragraphs of at most 70 words with a blank
  // line between them; a single <p> would undo that and hand the reader a wall.
  const paragraphs = text.split(/\n\s*\n/).map((t) => t.trim()).filter(Boolean);
  return (
    <Reveal className="narrow abstract">
      {paragraphs.map((t, i) => (
        <p key={i}>{t}</p>
      ))}
    </Reveal>
  );
}
