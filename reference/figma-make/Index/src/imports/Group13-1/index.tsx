import svgPaths from "./svg-hexv0gw1ci";

function Component() {
  return (
    <div className="absolute contents inset-0" data-name="图层 2">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 108 62.5862">
        <g id="å¾å± 1">
          <path d={svgPaths.p2c0a2800} fill="var(--fill-0, black)" id="Vector" />
          <path d={svgPaths.p19f2e740} fill="var(--fill-0, black)" id="Vector_2" />
        </g>
      </svg>
    </div>
  );
}

export default function Group() {
  return (
    <div className="contents relative size-full">
      <Component />
      <p className="[word-break:break-word] absolute font-['Glow_Sans_SC:Compressed_ExtraBold',sans-serif] inset-0 leading-[1.5] not-italic text-[22px] text-black text-center tracking-[4.4px]">关键词</p>
    </div>
  );
}