export default function Button() {
  return (
    <div className="bg-white content-stretch flex gap-[12px] items-center justify-center py-[4px] relative size-full" data-name="Button">
      <div className="relative shrink-0 size-[12px]" />
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[16px] text-black text-center tracking-[8px] whitespace-nowrap">
        <p className="leading-none">按钮</p>
      </div>
      <div className="relative shrink-0 size-[12px]" />
    </div>
  );
}