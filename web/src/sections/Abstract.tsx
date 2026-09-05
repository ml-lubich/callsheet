import { Reveal } from "../components/Reveal";
import { SkeletonLines } from "../components/Skeleton";

export function AbstractSkeleton() {
  return <SkeletonLines n={4} w="66ch" />;
}

export function Abstract({ text }: { text: string }) {
  return (
    <Reveal className="narrow abstract">
      <p>{text}</p>
    </Reveal>
  );
}
