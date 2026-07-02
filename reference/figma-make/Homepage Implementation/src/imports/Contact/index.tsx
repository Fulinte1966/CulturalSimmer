function Frame2() {
  return (
    <div className="[word-break:break-word] font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-x-[10px] grid-cols-[repeat(4,fit-content(100%))] grid-rows-[repeat(2,fit-content(100%))] h-full inline-grid leading-[0] not-italic relative shrink-0 text-black whitespace-nowrap">
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">白天 阴转多云</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">风向 北转南</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">风力 二、三级</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[0px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="text-[10px]">
          <span className="[word-break:break-word] font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none not-italic">最高温度</span>
          <span className="[word-break:break-word] font-['LXGW_Neo_XiHei_Screen:Regular',sans-serif] leading-none not-italic" style={{ fontFeatureSettings: '"hwid"' }}>{` `}</span>
          <span className="leading-none">24度</span>
        </p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">夜间 晴转多云</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">风向 南转北</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none">风力 一、二级</p>
      </div>
      <div className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[0px]" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="text-[10px]">
          <span className="[word-break:break-word] font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none not-italic" style={{ fontFeatureSettings: '"hwid"' }}>
            最低温度
          </span>
          <span className="[word-break:break-word] font-['LXGW_Neo_XiHei_Screen:Regular',sans-serif] leading-none not-italic" style={{ fontFeatureSettings: '"hwid"' }}>{` `}</span>
          <span className="leading-none">11度</span>
        </p>
      </div>
    </div>
  );
}

function Frame() {
  return (
    <div className="[word-break:break-word] content-stretch flex font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-[10px] items-center justify-center leading-[0] not-italic relative shrink-0 text-[10px] text-black text-center whitespace-nowrap">
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none mb-0">25日</p>
        <p className="leading-none">晴转多云</p>
      </div>
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none mb-0">26日</p>
        <p className="leading-none">多云转阴</p>
      </div>
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none mb-0">27日</p>
        <p className="leading-none">阴有雨</p>
      </div>
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex gap-[10px] items-center relative shrink-0">
      <div className="[word-break:break-word] flex flex-col font-['Source_Han_Sans_SC:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[10px] text-black whitespace-nowrap" style={{ fontFeatureSettings: '"hwid"' }}>
        <p className="leading-none mb-0">北京地区</p>
        <p className="leading-none">天气预报</p>
      </div>
      <div className="flex flex-row items-center self-stretch">
        <Frame2 />
      </div>
      <Frame />
    </div>
  );
}

export default function Contact() {
  return (
    <div className="bg-[rgba(255,255,255,0)] content-stretch flex gap-[20px] items-center justify-center px-[302px] relative size-full" data-name="Contact">
      <div className="[word-break:break-word] flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[0px] text-black whitespace-nowrap">
        <p className="font-['Source_Han_Sans_SC:Medium',sans-serif] text-[10px]">
          <span className="leading-none">本报地址：国内　霹雳放映站・</span>
          <a className="[text-decoration-skip-ink:none] [text-underline-position:from-font] cursor-pointer decoration-from-font decoration-solid leading-none underline" href="https://space.bilibili.com/3494350898072545" target="_blank">
            <span className="[text-decoration-skip-ink:none] [text-underline-position:from-font] decoration-from-font decoration-solid underline" href="https://space.bilibili.com/3494350898072545" target="_blank">
              走火放映室
            </span>
          </a>
          <span className="leading-none">{`　国外　优博放映站・`}</span>
          <a className="[text-decoration-skip-ink:none] [text-underline-position:from-font] cursor-pointer decoration-from-font decoration-solid leading-none underline" href="https://www.youtube.com/@Fulinte1966" target="_blank">
            <span className="[text-decoration-skip-ink:none] [text-underline-position:from-font] decoration-from-font decoration-solid underline" href="https://www.youtube.com/@Fulinte1966" target="_blank">
              弗林特放映室
            </span>
          </a>
        </p>
      </div>
      <div className="flex h-[16px] items-center justify-center relative shrink-0 w-0">
        <div className="flex-none rotate-90">
          <div className="h-0 relative w-[16px]">
            <div className="absolute inset-[-1px_0_0_0]">
              <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16 1">
                <line id="Line 261" stroke="var(--stroke-0, black)" x2="16" y1="0.5" y2="0.5" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      <Frame1 />
    </div>
  );
}