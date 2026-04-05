import React from "react";
import { Sparkles, ChevronRight } from "lucide-react";

export default function SectionHeader({
  title,
  subtitle,
  right,
  dotColor = "gold",
  eyebrow,
  compact = false,
}) {
  return (
    <div className={`afcfta-sectionHead ${compact ? "compact" : ""}`}>
      <div className="left">
        <div className="afcfta-sectionHead-mark">
          <span className={`afcfta-badgeDot ${dotColor}`} />
        </div>

        <div className="afcfta-sectionHead-copy">
          {eyebrow ? (
            <div className="afcfta-sectionHead-eyebrow">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{eyebrow}</span>
            </div>
          ) : null}

          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>

      {right ? <div className="afcfta-sectionHead-right">{right}</div> : null}
    </div>
  );
}
