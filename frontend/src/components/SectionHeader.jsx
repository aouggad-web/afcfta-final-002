import React from "react";

export default function SectionHeader({ title, subtitle, right, dotColor = "gold" }) {
  return (
    <div className="afcfta-sectionHead">
      <div className="left">
        <span className={`afcfta-badgeDot ${dotColor}`} />
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      <div>{right}</div>
    </div>
  );
}
