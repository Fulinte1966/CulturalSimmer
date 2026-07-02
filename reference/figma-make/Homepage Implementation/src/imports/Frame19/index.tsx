function Frame() {
  return (
    <div className="bg-white content-stretch flex flex-col h-[192px] items-center justify-center py-[19px] relative rounded-[2px] shrink-0 w-full">
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:CompactBold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[24px] text-black text-center w-full">
        <p className="leading-[1.75]">新书速递</p>
      </div>
    </div>
  );
}

export default function Frame1() {
  return (
    <div className="content-stretch flex flex-col items-center justify-center px-[6px] py-[12px] relative size-full">
      <Frame />
    </div>
  );
}