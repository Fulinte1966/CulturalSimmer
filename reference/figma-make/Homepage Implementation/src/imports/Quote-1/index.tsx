function Title() {
  return (
    <div className="absolute content-stretch flex flex-col items-center justify-center left-0 right-0 top-0" data-name="Title">
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:WideBold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[20px] text-white w-[24px]">
        <p className="leading-[1.25]">毛主席语录</p>
      </div>
    </div>
  );
}

function Frame() {
  return (
    <div className="h-[115px] relative shrink-0 w-[30px]">
      <Title />
    </div>
  );
}

function Quotation() {
  return (
    <div className="bg-white content-stretch flex flex-[1_0_0] flex-col h-full items-center justify-center min-w-px relative" data-name="Quotation">
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:CompactRegular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[#e22626] text-[0px] tracking-[8px] whitespace-nowrap">
        <p className="text-[32px] whitespace-pre">
          <span className="leading-[1.25]">{`　　你们要关心国家大`}</span>
          <span className="leading-[1.25]">事</span>
          <span className="leading-[1.25]">
            <br aria-hidden />
            要把无产阶级文化大革
          </span>
          <span className="leading-[1.25]">命</span>
          <span className="leading-[1.25]">
            <br aria-hidden />
            进行到底！
          </span>
        </p>
      </div>
    </div>
  );
}

export default function Quote() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center p-[6px] relative rounded-[8px] size-full" data-name="Quote">
      <Frame />
      <Quotation />
    </div>
  );
}