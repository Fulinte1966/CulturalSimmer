import svgPaths from "./svg-zn14avt4wu";

function Group() {
  return (
    <div className="-translate-x-1/2 -translate-y-1/2 absolute h-[4px] left-1/2 top-1/2 w-[10px]">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 4">
        <g id="Group 9">
          <rect fill="var(--fill-0, black)" height="4" id="Rectangle 10" width="2" x="2.66666" />
          <rect fill="var(--fill-0, black)" height="4" id="Rectangle 13" width="2" x="8.00001" />
          <rect fill="var(--fill-0, black)" height="4" id="Rectangle 8" width="0.666667" />
          <rect fill="var(--fill-0, black)" height="4" id="Rectangle 11" width="0.666667" x="5.33332" />
          <rect fill="var(--fill-0, black)" height="4" id="Rectangle 9" width="0.666667" x="1.33335" />
          <path d={svgPaths.p8c6b72} fill="var(--fill-0, black)" id="Rectangle 12" />
        </g>
      </svg>
    </div>
  );
}

function BorderFont1() {
  return (
    <div className="absolute left-0 overflow-clip size-[12px] top-0" data-name="Border Font 1">
      <Group />
    </div>
  );
}

function Rectangle({ className }: { className?: string }) {
  return <div className={className || "absolute left-0 size-[12px] top-0"} />;
}

export default function BorderFont() {
  return (
    <div className="contents relative size-full" data-name="BorderFont1">
      <BorderFont1 />
      <Rectangle />
    </div>
  );
}