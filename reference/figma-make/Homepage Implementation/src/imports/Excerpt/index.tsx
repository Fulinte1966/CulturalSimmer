function Frame() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px relative w-full">
      <div className="flex flex-col items-center overflow-clip rounded-[inherit] size-full">
        <div className="content-stretch flex flex-col items-center p-[12px] relative size-full">
          <div className="[word-break:break-word] font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-[0] not-italic relative shrink-0 text-[12px] text-black w-full whitespace-pre-wrap" style={{ fontFeatureSettings: '"dlig"' }}>
            <p className="leading-[1.5] mb-0">一、学一点政治经济学</p>
            <p className="leading-[1.5] mb-0">二、资本主义以前的社会经济制度</p>
            <p className="leading-[1.5] mb-0">{`　1. 原始公社建立了人类历史上最早的生产关系`}</p>
            <p className="leading-[1.5] mb-0">{`　2. 奴隶制是历史上最古老的剥削制度`}</p>
            <p className="leading-[1.5]">{`　3. 封建制度是又一个阶级对抗的剥削制度`}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Excerpt() {
  return (
    <div className="content-stretch flex flex-col items-center justify-center p-[12px] relative size-full" data-name="Excerpt">
      <Frame />
    </div>
  );
}