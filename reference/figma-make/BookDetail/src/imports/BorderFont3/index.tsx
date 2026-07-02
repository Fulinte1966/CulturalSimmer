function Frame() {
  return (
    <div className="h-[10.647px] relative shrink-0 w-px">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1 10.6471">
        <g id="Frame 6">
          <ellipse cx="0.5" cy="0.470588" fill="var(--fill-0, black)" id="Ellipse 1" rx="0.5" ry="0.470588" />
          <ellipse cx="0.5" cy="2.41176" fill="var(--fill-0, black)" id="Ellipse 2" rx="0.5" ry="0.470588" />
          <ellipse cx="0.5" cy="4.35294" fill="var(--fill-0, black)" id="Ellipse 3" rx="0.5" ry="0.470588" />
          <ellipse cx="0.5" cy="6.29412" fill="var(--fill-0, black)" id="Ellipse 4" rx="0.5" ry="0.470588" />
          <ellipse cx="0.5" cy="8.23529" fill="var(--fill-0, black)" id="Ellipse 5" rx="0.5" ry="0.470588" />
          <ellipse cx="0.5" cy="10.1765" fill="var(--fill-0, black)" id="Ellipse 6" rx="0.5" ry="0.470588" />
        </g>
      </svg>
    </div>
  );
}

function Frame1() {
  return (
    <div className="h-[10.647px] relative shrink-0 w-[0.941px]">
      <div className="absolute inset-[0_-3.12%]">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1 10.6471">
          <g id="Frame 7">
            <ellipse cx="0.5" cy="0.470588" fill="var(--fill-0, black)" id="Ellipse 1" rx="0.5" ry="0.470588" />
            <ellipse cx="0.5" cy="2.41176" fill="var(--fill-0, black)" id="Ellipse 2" rx="0.5" ry="0.470588" />
            <ellipse cx="0.5" cy="4.35294" fill="var(--fill-0, black)" id="Ellipse 3" rx="0.5" ry="0.470588" />
            <ellipse cx="0.5" cy="6.29412" fill="var(--fill-0, black)" id="Ellipse 4" rx="0.5" ry="0.470588" />
            <ellipse cx="0.5" cy="8.23529" fill="var(--fill-0, black)" id="Ellipse 5" rx="0.5" ry="0.470588" />
            <ellipse cx="0.5" cy="10.1765" fill="var(--fill-0, black)" id="Ellipse 6" rx="0.5" ry="0.470588" />
          </g>
        </svg>
      </div>
    </div>
  );
}

function Frame2() {
  return (
    <div className="-translate-x-1/2 -translate-y-1/2 absolute content-stretch flex gap-[2px] items-center left-1/2 top-[calc(50%+0.07px)]">
      <Frame />
      <Frame1 />
    </div>
  );
}

function BorderFont() {
  return (
    <div className="-translate-x-1/2 absolute left-0 overflow-clip size-[12px] top-0" data-name="Border Font 2">
      <Frame2 />
    </div>
  );
}

function Rectangle({ className }: { className?: string }) {
  return <div className={className || "absolute left-0 size-[12px] top-0"} />;
}

export default function BorderFont1() {
  return (
    <div className="contents relative size-full" data-name="BorderFont3">
      <BorderFont />
      <Rectangle />
    </div>
  );
}