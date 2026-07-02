import svgPaths from "./svg-6u4bx1v7h9";
import imgHead from "./bdc20ccc98ab52675df59e7408596c12e994f9b2.png";
import imgBook from "./5cb65d4db8502f46607eb2b01399f29ad28841e3.png";

function Grid() {
  return <div className="-translate-x-1/2 -translate-y-1/2 absolute bg-white h-[912px] left-1/2 top-[calc(50%+4px)] w-[1152px]" data-name="Grid" />;
}

function Component() {
  return (
    <div className="absolute contents right-[12px] top-[39.56px]" data-name="图层 1">
      <div className="absolute h-[66.888px] right-[12px] top-[39.56px] w-[48px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 48 66.8879">
          <path d={svgPaths.p133d2b0} fill="var(--fill-0, #D52B28)" id="Vector" />
        </svg>
      </div>
    </div>
  );
}

function Component1() {
  return (
    <div className="absolute contents right-[12px] top-[39.56px]" data-name="图层 2">
      <Component />
    </div>
  );
}

function Group1() {
  return (
    <div className="[word-break:break-word] absolute contents font-['Glow_Sans_SC:Compressed_ExtraBold',sans-serif] leading-[0] not-italic right-[20.48px] text-[16px] text-center top-[51.72px]">
      <div className="-translate-y-1/2 absolute flex flex-col h-[24.323px] justify-center right-[33.65px] text-white top-[63.88px] translate-x-1/2 w-[26.35px]">
        <p className="leading-[1.5]">勘误</p>
      </div>
      <div className="-translate-y-1/2 absolute flex flex-col h-[24.323px] justify-center right-[33.65px] text-black top-[63.88px] translate-x-1/2 w-[26.35px]">
        <p className="leading-[1.5]">勘误</p>
      </div>
    </div>
  );
}

function Group2() {
  return (
    <div className="absolute contents right-[12px] top-[39.56px]">
      <Component1 />
      <Group1 />
    </div>
  );
}

function Proofreading() {
  return (
    <div className="absolute contents right-[12px] top-[39.56px]" data-name="Proofreading">
      <Group2 />
    </div>
  );
}

function Group() {
  return (
    <div className="aspect-[274.0164489746094/115] h-full relative shrink-0">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 42.8895 18">
        <g id="Group 5">
          <path d={svgPaths.p5042200} fill="var(--fill-0, black)" id="Vector" />
          <path d={svgPaths.p3e61b900} fill="var(--fill-0, black)" id="Vector_2" />
          <path d={svgPaths.p451800} fill="var(--fill-0, black)" id="Vector_3" />
          <path d={svgPaths.pbe16900} fill="var(--fill-0, black)" id="Vector_4" />
          <path d={svgPaths.p2b1e9a00} fill="var(--fill-0, black)" id="Vector_5" />
          <path d={svgPaths.p3e22e40} fill="var(--fill-0, black)" id="Vector_6" />
          <path d={svgPaths.p8156200} fill="var(--fill-0, black)" id="Vector_7" />
          <path d={svgPaths.p3566e800} fill="var(--fill-0, black)" id="Vector_8" />
        </g>
      </svg>
    </div>
  );
}

function Frame8() {
  return (
    <div className="content-stretch flex h-full items-center relative shrink-0">
      <Group />
    </div>
  );
}

function Cr() {
  return (
    <div className="content-stretch flex h-[18px] items-center justify-end relative shrink-0 w-[35px]" data-name="CR">
      <Frame8 />
    </div>
  );
}

function Time() {
  return (
    <div className="[word-break:break-word] bg-[rgba(255,255,255,0)] content-stretch flex font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-[12px] items-center justify-center leading-none not-italic overflow-clip py-[2px] relative shrink-0 text-[12px] text-black w-[159px] whitespace-nowrap" data-name="Time">
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] relative shrink-0">2026 年 6 月 24 日</p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] relative shrink-0">星期三</p>
    </div>
  );
}

function Header() {
  return (
    <div className="absolute content-stretch flex gap-[12px] items-center justify-end right-0 top-0 w-[204px]" data-name="Header">
      <Cr />
      <Time />
    </div>
  );
}

function Directory() {
  return (
    <div className="[word-break:break-word] absolute content-stretch flex font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] h-[18px] items-center justify-center leading-none left-0 not-italic overflow-clip text-[12px] text-black top-0 whitespace-nowrap" data-name="Directory">
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] relative shrink-0">主页</p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] relative shrink-0">・</p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] relative shrink-0">《政治经济学基础知识》（资本主义部分）</p>
    </div>
  );
}

function Head() {
  return (
    <div className="h-[36px] relative shrink-0 w-full" data-name="Head">
      <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgHead} />
      <Proofreading />
      <div className="absolute h-0 left-0 right-0 top-[24px]" data-name="Headline">
        <div className="absolute inset-[-2px_0_0_0]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1154 2">
            <line id="Headline" stroke="var(--stroke-0, black)" strokeWidth="2" x2="1154" y1="1" y2="1" />
          </svg>
        </div>
      </div>
      <Header />
      <Directory />
    </div>
  );
}

function Book() {
  return (
    <div className="content-stretch flex flex-col h-[480px] items-center justify-center relative shrink-0 w-[284px]" data-name="Book">
      <div className="aspect-[368.19964599609375/556] relative shrink-0 w-full" data-name="Book">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <img alt="" className="absolute h-[113.5%] left-0 max-w-none top-[-2.84%] w-full" src={imgBook} />
        </div>
      </div>
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col gap-[6px] items-center relative shrink-0 w-full">
      <div className="flex flex-col font-['寒蝉锦书宋:WideRegular',sans-serif] justify-center relative shrink-0 text-[36px] w-full" style={{ fontFeatureSettings: '"hwid", "fwid", "dlig"' }}>
        <p className="leading-none">青年自学丛书</p>
      </div>
      <div className="flex flex-col font-['寒蝉锦书宋:CompactRegular',sans-serif] justify-center relative shrink-0 text-[84px] w-full" style={{ fontFeatureSettings: '"hwid", "dlig"' }}>
        <p className="leading-none">政治经济学基础知识</p>
      </div>
      <div className="flex flex-col font-['寒蝉锦书宋:TextMedium',sans-serif] justify-center relative shrink-0 text-[40px] w-full" style={{ fontFeatureSettings: '"hwid", "fwid", "dlig"' }}>
        <p className="indent-[calc(1px_*_(0px-0.45*40px))] leading-none">（资本主义部分）</p>
      </div>
    </div>
  );
}

function Frame2() {
  return (
    <div className="content-stretch flex flex-col gap-[24px] items-center justify-center relative shrink-0 w-full">
      <Frame1 />
      <div className="flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center relative shrink-0 text-[24px] w-full" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="indent-[calc(1px_*_(0px-0.45*24px))] leading-none">《政治经济学基础知识》编写组编</p>
      </div>
    </div>
  );
}

function Frame9() {
  return (
    <div className="content-stretch flex gap-[10px] h-[12px] items-center relative shrink-0">
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">216 页</p>
      </div>
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">10.7 万字</p>
      </div>
      <div className="flex flex-col justify-center relative shrink-0" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">1.60 兆字节</p>
      </div>
    </div>
  );
}

function Frame10() {
  return (
    <div className="gap-x-[10px] gap-y-[2px] grid grid-cols-[repeat(2,minmax(0,1fr))] grid-rows-[repeat(1,minmax(0,1fr))] h-[12px] relative shrink-0 w-[184px]">
      <div className="flex flex-col justify-center justify-self-center relative self-center shrink-0" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">2026 年 6 月第 1 版</p>
      </div>
      <div className="flex flex-col justify-center justify-self-center relative self-center shrink-0" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">2026 年 6 月第 2 版</p>
      </div>
    </div>
  );
}

function Frame4() {
  return (
    <div className="content-stretch flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-[2px] h-[30px] items-center justify-center relative shrink-0 text-[10px]">
      <Frame9 />
      <Frame10 />
    </div>
  );
}

function Frame3() {
  return (
    <div className="content-stretch flex flex-col gap-[6px] items-center justify-center relative shrink-0 whitespace-nowrap">
      <div className="flex flex-col font-['Source_Han_Sans_SC:Medium',sans-serif] justify-center relative shrink-0 text-[12px] tracking-[12px]" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">上册</p>
      </div>
      <Frame4 />
      <div className="flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center relative shrink-0 text-[12px]" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">内部书号 F0/1:1</p>
      </div>
    </div>
  );
}

function Info() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[18px] items-center justify-center leading-[0] not-italic relative shrink-0 text-black text-center w-full" data-name="Info">
      <Frame2 />
      <div className="flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center relative shrink-0 size-[12px] text-[12px]" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-none">＊</p>
      </div>
      <Frame3 />
    </div>
  );
}

function Component3() {
  return (
    <div className="absolute inset-[0_0.01%_0.07%_0]" data-name="图层 1">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 82.6855 43.6715">
        <g id="å¾å± 1">
          <path d={svgPaths.p17176300} fill="var(--fill-0, #D52B28)" id="Vector" />
          <path d={svgPaths.p28500400} fill="var(--fill-0, #D52B28)" id="Vector_2" />
          <path d={svgPaths.p2da36980} fill="var(--fill-0, #D52B28)" id="Vector_3" />
          <path d={svgPaths.p17fd4900} fill="var(--fill-0, #D52B28)" id="Vector_4" />
          <path d={svgPaths.p338f2680} fill="var(--fill-0, #D52B28)" id="Vector_5" />
        </g>
      </svg>
    </div>
  );
}

function Component2() {
  return (
    <div className="absolute contents inset-[0_0.01%_0.07%_0]" data-name="图层 2">
      <Component3 />
    </div>
  );
}

function Component4() {
  return (
    <div className="col-1 h-[43.7px] ml-0 mt-0 overflow-clip relative row-1 w-[82.69px]" data-name="资源 61">
      <Component2 />
    </div>
  );
}

function Downlaod() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0" data-name="Downlaod">
      <Component4 />
      <p className="[word-break:break-word] col-1 font-['Glow_Sans_SC:Compressed_ExtraBold',sans-serif] leading-[1.5] ml-[33px] mt-[9px] not-italic relative row-1 text-[16px] text-black text-center tracking-[4px] whitespace-nowrap">传阅</p>
    </div>
  );
}

function Frame7() {
  return (
    <div className="content-stretch flex flex-col items-start relative shrink-0 w-[108px]">
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

function Frame6() {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0">
      <Downlaod />
      <Frame7 />
    </div>
  );
}

function Abstract() {
  return (
    <div className="[word-break:break-word] content-stretch flex flex-col gap-[18px] items-center justify-center not-italic relative shrink-0 text-[12px] text-black w-full" data-name="Abstract">
      <p className="font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none relative shrink-0 text-center tracking-[12px] whitespace-nowrap" style={{ fontFeatureSettings: '"dlig"' }}>
        内容提要
      </p>
      <div className="font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-[0] min-w-full relative shrink-0 w-[min-content]" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="indent-[24px] leading-[1.5] mb-0">再明冰反青帶丁沒，乙壯畫足請雨快：頭錯虎假，點路陽邊記比兒千實穿害只法一息羊放共助，雞種半師少林身杯杯良，幼爸吧話夏息頁姐信助更嗎麼相秋他法隻，是兔雨。</p>
        <p className="indent-[24px] leading-[1.5] mb-0">汁女把昔，父拉黑原飯孝彩斤抱根意干現：房肖後位麻魚年乾卜和冒、斥免發就包做工足而光子。葉二雨乍林對斤真止胡外穴她化，木物故頭長色，害苦晚得動請。</p>
        <p className="indent-[24px] leading-[1.5] mb-0">禾共大書快司母服愛點呀登？頁勿菜秋戊良昌笑貓魚方南各掃虎！車音內笑蛋行。甲石後占玉昌免正內個幫吹幸穴地木十嗎者斤：讀喜根時很丁隻足即讀您：兒綠瓜親有几連今什三苗蝴；歌訴亮泉土一借，免亭三相松而校彩。</p>
        <p className="indent-[24px] leading-[1.5]">牙種那喜從加？久春乙目這豆牠五，苗而泉屋怪時，布上右姊上去水汁問長。立菜三古生天象心好，屋十在。跑方吧汁。</p>
      </div>
    </div>
  );
}

function Frame11() {
  return (
    <div className="content-stretch flex flex-col items-center justify-center relative shrink-0 w-full">
      <div className="[word-break:break-word] font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-[0] not-italic relative shrink-0 text-[12px] text-black whitespace-nowrap" style={{ fontFeatureSettings: '"dlig"' }}>
        <p className="leading-[1.5] mb-0 whitespace-pre">一、学一点政治经济学</p>
        <p className="leading-[1.5] mb-0 whitespace-pre">二、资本主义以前的社会经济制度</p>
        <p className="leading-[1.5] mb-0 whitespace-pre">{`　1. 原始公社建立了人类历史上最早的生产关系`}</p>
        <p className="leading-[1.5] mb-0 whitespace-pre">{`　2. 奴隶制是历史上最古老的剥削制度`}</p>
        <p className="leading-[1.5] whitespace-pre">{`　3. 封建制度是又一个阶级对抗的剥削制度`}</p>
      </div>
    </div>
  );
}

function Soc() {
  return (
    <div className="content-stretch flex flex-col gap-[18px] items-center justify-center relative shrink-0 w-full" data-name="Soc">
      <p className="[word-break:break-word] font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none not-italic relative shrink-0 text-[12px] text-black text-center tracking-[12px] whitespace-nowrap" style={{ fontFeatureSettings: '"dlig"' }}>
        目录大纲
      </p>
      <Frame11 />
    </div>
  );
}

function Intro() {
  return (
    <div className="content-stretch flex flex-col gap-[24px] items-center justify-center relative shrink-0 w-[540px]" data-name="Intro">
      <Abstract />
      <Soc />
    </div>
  );
}

function Text() {
  return (
    <div className="content-stretch flex flex-col gap-[24px] items-center relative shrink-0 w-[660px]" data-name="Text">
      <Info />
      <Frame6 />
      <div className="flex h-[12px] items-center justify-center relative shrink-0 w-[564px]">
        <div className="flex-none rotate-90">
          <div className="h-[564px] relative w-[12px]" data-name="Borderline" />
        </div>
      </div>
      <Intro />
    </div>
  );
}

function Frame5() {
  return (
    <div className="content-stretch flex gap-[48px] items-start justify-center relative shrink-0">
      <Book />
      <Text />
    </div>
  );
}

function Frame() {
  return (
    <div className="-translate-x-1/2 absolute content-stretch flex flex-col gap-[84px] items-center justify-center left-1/2 top-[25px] w-[1154px]" data-name="Frame">
      <Head />
      <Frame5 />
    </div>
  );
}

export default function Details() {
  return (
    <div className="bg-white relative size-full" data-name="Details">
      <Grid />
      <Frame />
    </div>
  );
}