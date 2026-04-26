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
        <div className="afcfta-sectionHead-copy">
          <div className="section-label">
            {eyebrow ? (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>{eyebrow}</span>
              </>
            ) : (
              <span className={`afcfta-badgeDot ${dotColor}`} />
            )}
          </div>
          <h2 className="section-title">{title}</h2>
          {subtitle ? <p className="section-desc">{subtitle}</p> : null}
        </div>
      </div>

      {right ? <div className="afcfta-sectionHead-right">{right}</div> : null}
    </div>
  );
}
