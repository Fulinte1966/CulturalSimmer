function Rectangle({ className }: { className?: string }) {
  return <div className={className || "relative size-[12px]"} />;
}
type ButtonProps = {
  className?: string;
  property1?: "Default" | "Variant2";
};

export default function Button({ className, property1 = "Default" }: ButtonProps) {
  return (
    <div className={className || "bg-white content-stretch flex gap-[12px] items-center justify-center py-[4px] relative"}>
      <Rectangle className="relative shrink-0 size-[12px]" />
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[16px] text-black text-center tracking-[8px] whitespace-nowrap">
        <p className={`leading-none ${property1 === "Variant2" ? "[text-underline-position:from-font] decoration-[6.25%] decoration-solid underline" : ""}`}>按钮</p>
      </div>
      <Rectangle className="relative shrink-0 size-[12px]" />
    </div>
  );
}