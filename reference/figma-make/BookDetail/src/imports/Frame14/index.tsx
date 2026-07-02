export default function Frame() {
  return (
    <div className="content-stretch flex flex-col items-start relative size-full">
      <div className="bg-white content-stretch flex gap-[12px] items-center justify-center py-[4px] relative shrink-0 w-full" data-name="Button">
        <div className="relative shrink-0 size-[12px]" />
        <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[12px] text-black text-center whitespace-nowrap">
          <p className="leading-none">基核技术站</p>
        </div>
        <div className="relative shrink-0 size-[12px]" />
      </div>
      <div className="bg-white content-stretch flex gap-[12px] items-center justify-center py-[4px] relative shrink-0 w-full" data-name="Button">
        <div className="relative shrink-0 size-[12px]" />
        <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[12px] text-black text-center whitespace-nowrap">
          <p className="leading-none">择览资料站</p>
        </div>
        <div className="relative shrink-0 size-[12px]" />
      </div>
    </div>
  );
}