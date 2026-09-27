import clsx from "clsx";
import {
  CONFLICT_LABEL_BADGE_CLASS,
  CONFLICT_LABEL_TEXT,
} from "@/lib/reasoning-states";
import type { ConflictTypeLabel } from "@/types/api";

export function ConflictBadge({ label }: { label: ConflictTypeLabel }) {
  return (
    <span
      className={clsx(CONFLICT_LABEL_BADGE_CLASS[label])}
      data-testid={`conflict-badge-${label}`}
    >
      {CONFLICT_LABEL_TEXT[label]}
    </span>
  );
}
