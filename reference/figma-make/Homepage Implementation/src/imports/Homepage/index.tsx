import svgPaths from "./svg-a5i94psk2v";
import imgPagesFromF01Pdf1 from "./bed415caa8df8d0a09e50b2dc1031c35124978c8.png";

function Group() {
  return (
    <div className="aspect-[274.0164489746094/113.02094268798828] h-full relative shrink-0">
      <svg
        className="absolute block inset-0 size-full"
        fill="none"
        preserveAspectRatio="none"
        viewBox="0 0 278.815 115"
      >
        <g id="Group 5">
          <path
            d={svgPaths.p873f80}
            fill="var(--fill-0, #E22626)"
            id="Vector"
          />
          <path
            d={svgPaths.p1b2d1a80}
            fill="var(--fill-0, #E22626)"
            id="Vector_2"
          />
          <path
            d={svgPaths.p914a340}
            fill="var(--fill-0, #E22626)"
            id="Vector_3"
          />
          <path
            d={svgPaths.p34ec7c00}
            fill="var(--fill-0, #E22626)"
            id="Vector_4"
          />
          <path
            d={svgPaths.p2e446900}
            fill="var(--fill-0, #E22626)"
            id="Vector_5"
          />
          <path
            d={svgPaths.p214b09c0}
            fill="var(--fill-0, #E22626)"
            id="Vector_6"
          />
          <path
            d={svgPaths.p27904878}
            fill="var(--fill-0, #E22626)"
            id="Vector_7"
          />
          <path
            d={svgPaths.p120ee8c0}
            fill="var(--fill-0, #E22626)"
            id="Vector_8"
          />
        </g>
      </svg>
    </div>
  );
}

function Frame8() {
  return (
    <div className="content-stretch flex h-full items-center justify-center relative shrink-0">
      <Group />
    </div>
  );
}

function Cr() {
  return (
    <div
      className="content-stretch flex h-[115px] items-center justify-end relative shrink-0 w-[228px]"
      data-name="CR"
    >
      <Frame8 />
    </div>
  );
}

function Time() {
  return (
    <div
      className="[word-break:break-word] bg-[rgba(255,255,255,0)] content-stretch flex gap-[16px] items-center justify-center leading-[1.5] not-italic relative shrink-0 text-[16px] text-black w-full whitespace-nowrap"
      data-name="Time"
    >
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['Source_Han_Sans_SC:Medium',sans-serif] relative shrink-0">
        2026 年 6 月 24 日
      </p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['Source_Han_Sans_SC:Medium',sans-serif] relative shrink-0">
        星期三
      </p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['Zhuque_Fangsong_(technical_preview):Regular',sans-serif] relative shrink-0">
        农历丙午年五月初十
      </p>
    </div>
  );
}

function Logo() {
  return (
    <div
      className="content-stretch flex flex-col gap-[12px] items-center justify-center relative shrink-0 w-[354px]"
      data-name="Logo"
    >
      <Cr />
      <Time />
    </div>
  );
}

function Title() {
  return (
    <div
      className="absolute content-stretch flex flex-col items-center justify-center left-0 right-0 top-0"
      data-name="Title"
    >
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:WideBold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[20px] text-white w-[24px]">
        <p className="leading-[1.25]">毛主席语录</p>
      </div>
    </div>
  );
}

function Frame10() {
  return (
    <div className="bg-[#e22626] h-[115px] relative shrink-0 w-[30px]">
      <Title />
    </div>
  );
}

function Quotation() {
  return (
    <div
      className="bg-white content-stretch flex flex-[1_0_0] flex-col h-full items-center justify-center min-w-px relative"
      data-name="Quotation"
    >
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

function Quote() {
  return (
    <div
      className="content-stretch flex gap-[6px] h-[154px] items-center justify-center p-[6px] relative rounded-[8px] shrink-0 w-[528px]"
      style={{
        backgroundImage:
          "repeating-linear-gradient(45deg, #e22626 0px, #e22626 1px, transparent 1px, transparent 3px)",
      }}
      data-name="Quote"
    >
      <Frame10 />
      <Quotation />
    </div>
  );
}

function Head() {
  return (
    <div
      className="content-stretch flex gap-[48px] items-center justify-center py-[6px] relative shrink-0 w-full"
      data-name="Head"
    >
      <Logo />
      <Quote />
    </div>
  );
}

function Frame4() {
  return (
    <div className="bg-white border-y border-black content-stretch flex flex-col h-[192px] items-center justify-center py-[19px] relative shrink-0 w-full">
      <div className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] flex flex-col font-['寒蝉锦书宋:CompactBold',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[24px] text-black text-center w-full">
        <p className="leading-[1.75]">新书速递</p>
      </div>
    </div>
  );
}

function Frame5() {
  return (
    <div
      className="content-stretch flex flex-col items-center justify-center overflow-clip px-[6px] py-[12px] relative shrink-0 w-[36px]"
      style={{
        backgroundImage:
          "repeating-linear-gradient(0deg, #000 0px, #000 1px, transparent 1px, transparent 3px)",
      }}
    >
      <Frame4 />
    </div>
  );
}

function Frame9() {
  return (
    <div className="bg-white flex-[1_0_0] min-h-px relative w-full">
      <div className="flex flex-col items-center overflow-clip rounded-[inherit] size-full">
        <div className="content-stretch flex flex-col items-center p-[12px] relative size-full">
          <div
            className="[word-break:break-word] font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-[0] not-italic relative shrink-0 text-[12px] text-black w-full whitespace-pre-wrap"
            style={{ fontFeatureSettings: '"dlig"' }}
          >
            <p className="leading-[1.5] mb-0">
              一、学一点政治经济学
            </p>
            <p className="leading-[1.5] mb-0">
              二、资本主义以前的社会经济制度
            </p>
            <p className="leading-[1.5] mb-0">{`　1. 原始公社建立了人类历史上最早的生产关系`}</p>
            <p className="leading-[1.5] mb-0">{`　2. 奴隶制是历史上最古老的剥削制度`}</p>
            <p className="leading-[1.5]">{`　3. 封建制度是又一个阶级对抗的剥削制度`}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Excerpt() {
  return (
    <div
      className="-translate-x-1/2 -translate-y-1/2 absolute content-stretch flex flex-col h-[408px] items-center justify-center left-[calc(50%+336px)] overflow-clip p-[12px] top-[calc(50%+1.5px)] w-[396px]"
      style={{
        backgroundImage:
          "repeating-linear-gradient(45deg, #000 0px, #000 1px, transparent 1px, transparent 3px)",
      }}
      data-name="Excerpt"
    >
      <Frame9 />
    </div>
  );
}

function Head1() {
  return (
    <div
      className="bg-white content-stretch flex flex-col gap-[14px] items-center justify-center leading-[1.5] relative shrink-0 text-center w-full"
      data-name="Head"
    >
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['寒蝉端黑宋:Wide_Light',sans-serif] relative shrink-0 text-[12px] w-full">
        青年自学丛书
      </p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['寒蝉锦书宋:Bold',sans-serif] relative shrink-0 text-[24px] w-full">
        政治经济学基础知识
      </p>
      <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] font-['寒蝉锦书宋:TextMedium',sans-serif] relative shrink-0 text-[12px] w-full">
        （资本主义部分）
      </p>
    </div>
  );
}

function Intro() {
  return (
    <div
      className="-translate-x-1/2 -translate-y-1/2 [word-break:break-word] absolute content-stretch flex flex-col gap-[18px] h-[408px] items-center justify-center left-[calc(50%-42px)] not-italic overflow-clip text-black top-[calc(50%+1.5px)] w-[336px]"
      data-name="Intro"
    >
      <Head1 />
      <div
        className="font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-[0] relative shrink-0 text-[12px] w-full"
        style={{ fontFeatureSettings: '"dlig"' }}
      >
        <p className="indent-[24px] leading-[1.5] mb-0">
          再明冰反青帶丁沒，乙壯畫足請雨快：頭錯虎假，點路陽邊記比兒千實穿害只法一息羊放共助，雞種半師少林身杯杯良，幼爸吧話夏息頁姐信助更嗎麼相秋他法隻，是兔雨。
        </p>
        <p className="indent-[24px] leading-[1.5] mb-0">
          汁女把昔，父拉黑原飯孝彩斤抱根意干現：房肖後位麻魚年乾卜和冒、斥免發就包做工足而光子。葉二雨乍林對斤真止胡外穴她化，木物故頭長色，害苦晚得動請。
        </p>
        <p className="indent-[24px] leading-[1.5] mb-0">
          禾共大書快司母服愛點呀登？頁勿菜秋戊良昌笑貓魚方南各掃虎！車音內笑蛋行。甲石後占玉昌免正內個幫吹幸穴地木十嗎者斤：讀喜根時很丁隻足即讀您：兒綠瓜親有几連今什三苗蝴；歌訴亮泉土一借，免亭三相松而校彩。
        </p>
        <p className="indent-[24px] leading-[1.5]">
          牙種那喜從加？久春乙目這豆牠五，苗而泉屋怪時，布上右姊上去水汁問長。立菜三古生天象心好，屋十在。跑方吧汁。
        </p>
      </div>
    </div>
  );
}

function Frame7() {
  return (
    <div className="relative shrink-0 size-[12px]">
      <svg
        className="absolute block inset-0 size-full"
        fill="none"
        preserveAspectRatio="none"
        viewBox="0 0 12 12"
      >
        <g id="Frame 24">
          <path
            d={svgPaths.p240fcd80}
            fill="var(--fill-0, black)"
            id="â"
          />
        </g>
      </svg>
    </div>
  );
}

function Frame6() {
  return (
    <div className="relative shrink-0 size-[12px]">
      <svg
        className="absolute block inset-0 size-full"
        fill="none"
        preserveAspectRatio="none"
        viewBox="0 0 12 12"
      >
        <g id="Frame 23">
          <path
            d={svgPaths.p240fcd80}
            fill="var(--fill-0, black)"
            id="â"
          />
        </g>
      </svg>
    </div>
  );
}

function BorderLine() {
  return (
    <div
      className="content-stretch flex items-center justify-center relative w-[395px]"
      data-name="Border line"
    >
      <Frame7 />
      {/* Middle segment uses BorderFont4 (double-dot column) tile from Components */}
      <div
        className="flex-[1_0_0] self-center overflow-hidden"
        style={{ height: "12px" }}
      >
        <svg
          width="100%"
          height="12"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <pattern
              id="borderWavyRule"
              x="0"
              y="0"
              width="12"
              height="12"
              patternUnits="userSpaceOnUse"
            >
              <g transform="translate(1, 4)">
                <path
                  d="M6.17068 1.25989L4.28875 1.77284C3.25527 2.05341 2.37775 2.18504 1.65619 2.16775C1.42451 2.16487 1.22455 2.12597 1.0563 2.05107C0.980801 2.01762 0.891929 1.92067 0.789678 1.76022C0.6882 1.60276 0.649471 1.44708 0.673492 1.29318C0.687692 1.21882 0.722509 1.14194 0.777943 1.06253C0.83415 0.986114 0.886483 0.929974 0.934943 0.894113C1.0249 0.830725 1.11704 0.805142 1.21136 0.817361C1.30567 0.829581 1.39263 0.883853 1.47222 0.980176C1.54667 1.06833 1.57692 1.15595 1.56297 1.24304C1.54979 1.33311 1.50659 1.43633 1.43336 1.55268C1.3707 1.6629 1.38356 1.73615 1.47194 1.77242C1.56109 1.81168 1.68814 1.82121 1.85307 1.80102C2.02084 1.78004 2.20885 1.73744 2.4171 1.67321C2.63101 1.60741 2.82934 1.54594 3.01207 1.4888C3.1948 1.43166 3.36194 1.37885 3.51349 1.33037C3.66787 1.2811 3.89776 1.21247 4.20317 1.12446C4.51141 1.03567 4.82288 0.947587 5.13756 0.860208L6.39205 0.511874C6.6472 0.441026 6.92014 0.368442 7.21085 0.29412C7.50156 0.219799 7.76083 0.15901 7.98866 0.111753C8.22009 0.066695 8.42472 0.0354817 8.60254 0.0181129C8.78113 0.00373041 8.96346 -0.00208681 9.14952 0.000661269C9.25363 0.00375957 9.37423 0.0294862 9.51131 0.0778412C9.65199 0.128395 9.75686 0.187296 9.8259 0.254544C9.89133 0.319592 9.93705 0.396517 9.96304 0.485319C9.99265 0.57632 10.0045 0.669058 9.99851 0.763532C9.99254 0.858007 9.98118 0.931577 9.96441 0.984244C9.93706 1.07826 9.86745 1.1616 9.75558 1.23427C9.64449 1.30993 9.53032 1.32082 9.41308 1.26696C9.35047 1.23633 9.29135 1.18394 9.23571 1.10977C9.18291 1.03481 9.14995 0.95434 9.13684 0.868363C9.12373 0.782385 9.13961 0.70276 9.18447 0.62949C9.22986 0.546473 9.24805 0.475807 9.23905 0.417493C9.23082 0.362166 9.20262 0.323587 9.15444 0.301759C9.10986 0.28213 9.05845 0.277201 9.00021 0.286972C8.92573 0.304453 8.83719 0.332236 8.73462 0.370321C8.63487 0.407619 8.39505 0.496615 8.01515 0.63731C7.63808 0.777218 7.30019 0.898246 7.00147 1.00039C6.7056 1.10175 6.42866 1.18825 6.17068 1.25989Z"
                  fill="black"
                />
                <path
                  d="M5.50408 3.09063L3.62216 3.60358C2.58867 3.88414 1.71115 4.01578 0.98959 3.99849C0.757917 3.99561 0.557954 3.95671 0.389701 3.8818C0.314206 3.84836 0.225334 3.75141 0.123083 3.59096C0.0216043 3.4335 -0.0171245 3.27782 0.00689655 3.12392C0.0210966 3.04956 0.0559138 2.97268 0.111348 2.89327C0.167554 2.81685 0.219887 2.76071 0.268348 2.72485C0.358309 2.66146 0.450446 2.63588 0.544761 2.6481C0.639076 2.66032 0.726031 2.71459 0.805626 2.81091C0.880071 2.89907 0.91032 2.98669 0.896373 3.07378C0.883198 3.16385 0.839996 3.26707 0.766768 3.38342C0.704107 3.49364 0.716966 3.56689 0.805345 3.60316C0.894496 3.64242 1.02154 3.65195 1.18648 3.63176C1.35425 3.61078 1.54226 3.56818 1.7505 3.50395C1.96442 3.43815 2.16274 3.37668 2.34547 3.31954C2.52821 3.2624 2.69534 3.20959 2.84689 3.16111C3.00127 3.11184 3.23117 3.0432 3.53657 2.9552C3.84482 2.86641 4.15628 2.77833 4.47097 2.69095L5.72546 2.34261C5.98061 2.27177 6.25354 2.19918 6.54425 2.12486C6.83497 2.05054 7.09424 1.98975 7.32206 1.94249C7.5535 1.89743 7.75812 1.86622 7.93594 1.84885C8.11454 1.83447 8.29686 1.82865 8.48292 1.8314C8.58703 1.8345 8.70763 1.86022 8.84471 1.90858C8.9854 1.95913 9.09026 2.01803 9.1593 2.08528C9.22474 2.15033 9.27045 2.22726 9.29645 2.31606C9.32605 2.40706 9.33787 2.4998 9.33191 2.59427C9.32595 2.68875 9.31458 2.76232 9.29781 2.81498C9.27046 2.90899 9.20086 2.99234 9.08899 3.06501C8.97789 3.14067 8.86372 3.15156 8.74649 3.0977C8.68388 3.06707 8.62475 3.01467 8.56912 2.9405C8.51632 2.86555 8.48336 2.78508 8.47025 2.6991C8.45713 2.61312 8.47301 2.5335 8.51788 2.46023C8.56326 2.37721 8.58145 2.30655 8.57246 2.24823C8.56423 2.1929 8.53602 2.15433 8.48784 2.1325C8.44327 2.11287 8.39186 2.10794 8.33361 2.11771C8.25913 2.13519 8.1706 2.16297 8.06802 2.20106C7.96828 2.23836 7.72845 2.32735 7.34855 2.46805C6.97148 2.60796 6.63359 2.72898 6.33488 2.83113C6.039 2.93249 5.76207 3.01899 5.50408 3.09063Z"
                  fill="black"
                />
              </g>
            </pattern>
          </defs>
          <rect
            width="100%"
            height="12"
            fill="url(#borderWavyRule)"
          />
        </svg>
      </div>
      <Frame6 />
    </div>
  );
}

function Book() {
  return (
    <div
      className="-translate-x-1/2 absolute bottom-[18px] left-[calc(50%-390px)] overflow-clip rounded-[8px] top-[18px] w-[288px]"
      data-name="Book"
    >
      <div
        className="absolute h-[408px] left-0 top-0 w-[288px]"
        data-name="Pages from F0.1.pdf 1"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Detail() {
  return (
    <div
      className="h-[444px] overflow-clip relative shrink-0 w-[1068px]"
      data-name="Detail"
    >
      <Excerpt />
      <Intro />
      <div className="-translate-x-1/2 -translate-y-1/2 absolute flex h-[395px] items-center justify-center left-[calc(50%-228px)] top-[calc(50%+0.5px)] w-[12px]">
        <div className="flex-none rotate-90">
          <BorderLine />
        </div>
      </div>
      <Book />
    </div>
  );
}

function Newsletter() {
  return (
    <div
      className="h-[461px] relative shrink-0 w-full"
      data-name="Newsletter"
    >
      <div className="flex flex-row items-center justify-center overflow-clip rounded-[inherit] size-full">
        <div className="content-stretch flex gap-[24px] items-center justify-center px-[12px] relative size-full">
          <Frame5 />
          <Detail />
        </div>
      </div>
    </div>
  );
}

function Book1() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Book2() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Book3() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Book4() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Book5() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function Book6() {
  return (
    <div
      className="content-stretch flex h-[238px] items-center justify-center overflow-clip relative rounded-[8px] shrink-0 w-[168px]"
      data-name="Book"
    >
      <div
        className="aspect-[173/246] h-full relative shrink-0"
        data-name="Pages from F0.1.pdf 2"
      >
        <img
          alt=""
          className="absolute inset-0 max-w-none object-cover pointer-events-none size-full"
          src={imgPagesFromF01Pdf1}
        />
      </div>
    </div>
  );
}

function BookList() {
  return (
    <div
      className="-translate-y-1/2 absolute content-stretch flex gap-[12px] items-center left-[180px] overflow-clip top-1/2 w-[984px]"
      data-name="Book List"
    >
      <Book1 />
      <Book2 />
      <Book3 />
      <Book4 />
      <Book5 />
      <Book6 />
    </div>
  );
}

function Mask1() {
  return (
    <div
      className="absolute bg-gradient-to-r from-[rgba(255,255,255,0)] h-[246px] left-[1140px] to-white top-0 w-[12px]"
      data-name="Mask"
    />
  );
}

function Head3() {
  return (
    <div
      className="col-1 h-[55.625px] ml-0 mt-0 overflow-clip relative row-1 w-[120px]"
      data-name="Head"
    >
      <div
        className="absolute inset-[-0.02%_-0.02%_0.07%_0.08%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 119.925 55.5969"
        >
          <path></path>
          <path></path>
          <path
            d={svgPaths.p3bdac4f0}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[60.92%_47.12%_36.57%_52.06%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.985746 1.39404"
        >
          <path
            d={svgPaths.p26229300}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[60.58%_48.44%_36.98%_50.79%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.927206 1.35441"
        >
          <path
            d={svgPaths.pfc16980}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[60.57%_51.49%_37.1%_47.71%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.950817 1.29578"
        >
          <path
            d={svgPaths.p3cd65100}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[60.72%_52.89%_37.01%_46.4%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.858145 1.26406"
        >
          <path
            d={svgPaths.p1d1b080}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[61.14%_50.1%_37.01%_49.16%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.8915 1.02625"
        >
          <path
            d={svgPaths.p3646c400}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[61.98%_59.49%_35.22%_39.59%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 1.09882 1.55628"
        >
          <path
            d={svgPaths.pa5f6161}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[64.03%_63.86%_32.98%_35.27%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 1.03615 1.66124"
        >
          <path
            d={svgPaths.pb748600}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[61.43%_58.06%_36.04%_41.07%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 1.03913 1.40682"
        >
          <path
            d={svgPaths.p267c6a80}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[63.29%_62.48%_33.81%_36.72%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.958119 1.61279"
        >
          <path
            d={svgPaths.p2d98ad40}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[62.71%_60.99%_34.72%_38.24%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.922987 1.4317"
        >
          <path
            d={svgPaths.p23195600}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[64.03%_39.57%_33.49%_59.55%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 1.05735 1.38168"
        >
          <path
            d={svgPaths.p2b361a80}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[62.82%_41.03%_34.7%_58.19%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.933615 1.37873"
        >
          <path
            d={svgPaths.p2dd2b540}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[65.02%_38.32%_32.46%_60.86%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.984809 1.39945"
        >
          <path
            d={svgPaths.p38be5240}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[61.98%_42.25%_35.6%_56.92%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 0.995169 1.34426"
        >
          <path
            d={svgPaths.padef700}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[66.33%_36.98%_31.52%_62.12%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 1.0817 1.19922"
        >
          <path
            d={svgPaths.p3fbfa000}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[68.1%_25.66%_20.54%_65.37%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 10.7699 6.31893"
        >
          <path
            d={svgPaths.p1462be80}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[63.56%_20.28%_28.38%_72.89%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 8.20196 4.48246"
        >
          <path
            d={svgPaths.p2be06a00}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[71.6%_23.64%_22.4%_73.61%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 3.29716 3.33508"
        >
          <path
            d={svgPaths.p10298a00}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[62.59%_73.42%_23.32%_19.56%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 8.42458 7.83735"
        >
          <path
            d={svgPaths.p20805300}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <div
        className="absolute inset-[64.53%_81.05%_31.3%_15.58%]"
        data-name="Vector"
      >
        <svg
          className="absolute block inset-0 size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 4.04974 2.32014"
        >
          <path
            d={svgPaths.p34b0e600}
            fill="var(--fill-0, black)"
            id="Vector"
          />
        </svg>
      </div>
      <p className="[word-break:break-word] absolute font-['Glow_Sans_SC:Compressed_ExtraBold',sans-serif] inset-[13.05%_12.75%_42.23%_12.96%] leading-[1.5] not-italic text-[16px] text-black text-center tracking-[4px]">
        上架书目
      </p>
    </div>
  );
}

function Head2() {
  return (
    <div
      className="grid-cols-[max-content] grid-rows-[max-content] inline-grid place-items-start relative"
      data-name="Head"
    >
      <Head3 />
    </div>
  );
}

function Mask2() {
  return (
    <div
      className="bg-gradient-to-r content-stretch flex flex-col from-[rgba(255,255,255,0)] gap-[18px] h-[245px] items-center justify-center relative to-[6.731%] to-white w-[164px]"
      data-name="Mask"
    >
      <div className="flex items-center justify-center leading-[0] relative shrink-0">
        <div className="-scale-y-100 flex-none rotate-180">
          <Head2 />
        </div>
      </div>
      <div className="flex items-center justify-center relative shrink-0">
        <div className="-scale-y-100 flex-none rotate-180">
          <div
            className="bg-white flex flex-row gap-[12px] items-center justify-center py-[4px] px-0 w-[88px] h-[20px]"
            data-name="Button"
          >
            {/* BorderFont5 (double-dot column) from Components-2 */}
            <div
              className="col-1 ml-0 mt-0 overflow-clip relative row-1 size-[12px]"
              data-name="Border Font 2"
            >
              <div className="-translate-x-1/2 -translate-y-1/2 absolute h-[8px] left-[calc(50%-1.41px)] top-1/2 w-[0.941px]">
                <svg
                  className="absolute block inset-0 size-full"
                  fill="none"
                  preserveAspectRatio="none"
                  viewBox="0 0 0.941178 8"
                >
                  <g id="Group 7">
                    <circle
                      cx="0.470588"
                      cy="0.470588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="1.88235"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="3.29412"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="4.70588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="6.11765"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="7.52941"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                  </g>
                </svg>
              </div>
              <div className="-translate-x-1/2 -translate-y-1/2 absolute h-[8px] left-[calc(50%+1.41px)] top-1/2 w-[0.941px]">
                <svg
                  className="absolute block inset-0 size-full"
                  fill="none"
                  preserveAspectRatio="none"
                  viewBox="0 0 0.941177 8"
                >
                  <g id="Group 7">
                    <circle
                      cx="0.470589"
                      cy="0.470588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="1.88238"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="3.29412"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="4.70588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="6.11765"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="7.52941"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                  </g>
                </svg>
              </div>
            </div>
            <p className="[text-box-edge:cap_alphabetic] [text-box-trim:trim-both] [word-break:break-word] font-['寒蝉锦书宋:Medium',sans-serif] leading-[1.5] not-italic relative shrink-0 text-[16px] text-black text-center tracking-[8px] whitespace-nowrap">
              索引
            </p>
            {/* BorderFont5 (double-dot column) from Components-2 */}
            <div
              className="col-1 ml-0 mt-0 overflow-clip relative row-1 size-[12px]"
              data-name="Border Font 2"
            >
              <div className="-translate-x-1/2 -translate-y-1/2 absolute h-[8px] left-[calc(50%-1.41px)] top-1/2 w-[0.941px]">
                <svg
                  className="absolute block inset-0 size-full"
                  fill="none"
                  preserveAspectRatio="none"
                  viewBox="0 0 0.941178 8"
                >
                  <g id="Group 7">
                    <circle
                      cx="0.470588"
                      cy="0.470588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="1.88235"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="3.29412"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="4.70588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="6.11765"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.47059"
                      cy="7.52941"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                  </g>
                </svg>
              </div>
              <div className="-translate-x-1/2 -translate-y-1/2 absolute h-[8px] left-[calc(50%+1.41px)] top-1/2 w-[0.941px]">
                <svg
                  className="absolute block inset-0 size-full"
                  fill="none"
                  preserveAspectRatio="none"
                  viewBox="0 0 0.941177 8"
                >
                  <g id="Group 7">
                    <circle
                      cx="0.470589"
                      cy="0.470588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="1.88238"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="3.29412"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="4.70588"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="6.11765"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                    <circle
                      cx="0.470588"
                      cy="7.52941"
                      fill="var(--fill-0, black)"
                      r="0.470588"
                    />
                  </g>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Mask() {
  return (
    <div
      className="absolute contents left-0 top-0"
      data-name="Mask"
    >
      <Mask1 />
      <div className="-translate-x-1/2 -translate-y-1/2 absolute flex h-[245px] items-center justify-center left-[calc(50%-494px)] top-[calc(50%-0.5px)] w-[164px]">
        <div className="-scale-y-100 flex-none rotate-180">
          <Mask2 />
        </div>
      </div>
    </div>
  );
}

function BookShelf() {
  return (
    <div
      className="h-[246px] overflow-clip relative shrink-0 w-full"
      data-name="Book Shelf"
    >
      <BookList />
      <Mask />
    </div>
  );
}

function Frame3() {
  return (
    <div className="[word-break:break-word] font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-x-[10px] grid-cols-[repeat(4,fit-content(100%))] grid-rows-[repeat(2,fit-content(100%))] h-full inline-grid leading-[0] not-italic relative shrink-0 text-black whitespace-nowrap">
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">白天 阴转多云</p>
      </div>
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">风向 北转南</p>
      </div>
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">风力 二、三级</p>
      </div>
      <div
        className="flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center justify-self-start relative self-start shrink-0 text-[0px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="text-[10px]">
          <span className="[word-break:break-word] font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none not-italic">
            最高温度
          </span>
          <span
            className="[word-break:break-word] font-['LXGW_Neo_XiHei_Screen:Regular',sans-serif] leading-none not-italic"
            style={{ fontFeatureSettings: '"hwid"' }}
          >{` `}</span>
          <span className="font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-none">
            24度
          </span>
        </p>
      </div>
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">夜间 晴转多云</p>
      </div>
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">风向 南转北</p>
      </div>
      <div
        className="flex flex-col justify-center justify-self-start relative self-start shrink-0 text-[10px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none">风力 一、二级</p>
      </div>
      <div
        className="flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center justify-self-start relative self-start shrink-0 text-[0px]"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="text-[10px]">
          <span
            className="[word-break:break-word] font-['Source_Han_Sans_SC:Medium',sans-serif] leading-none not-italic"
            style={{ fontFeatureSettings: '"hwid"' }}
          >
            最低温度
          </span>
          <span
            className="[word-break:break-word] font-['LXGW_Neo_XiHei_Screen:Regular',sans-serif] leading-none not-italic"
            style={{ fontFeatureSettings: '"hwid"' }}
          >{` `}</span>
          <span className="font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] leading-none">
            11度
          </span>
        </p>
      </div>
    </div>
  );
}

function Frame1() {
  return (
    <div className="[word-break:break-word] content-stretch flex font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] gap-[10px] items-center justify-center leading-[0] not-italic relative shrink-0 text-[10px] text-black text-center whitespace-nowrap">
      <div
        className="flex flex-col justify-center relative shrink-0"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none mb-0">25日</p>
        <p className="leading-none">晴转多云</p>
      </div>
      <div
        className="flex flex-col justify-center relative shrink-0"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none mb-0">26日</p>
        <p className="leading-none">多云转阴</p>
      </div>
      <div
        className="flex flex-col justify-center relative shrink-0"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none mb-0">27日</p>
        <p className="leading-none">阴有雨</p>
      </div>
    </div>
  );
}

function Frame2() {
  return (
    <div className="content-stretch flex gap-[10px] items-center relative shrink-0">
      <div
        className="[word-break:break-word] flex flex-col font-['Source_Han_Sans_SC:Medium',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[10px] text-black whitespace-nowrap"
        style={{ fontFeatureSettings: '"hwid"' }}
      >
        <p className="leading-none mb-0">北京地区</p>
        <p className="leading-none">天气预报</p>
      </div>
      <Frame3 />
      <Frame1 />
    </div>
  );
}

function Contact() {
  return (
    <div
      className="bg-[rgba(255,255,255,0)] relative shrink-0 w-full"
      data-name="Contact"
    >
      <div className="flex flex-row items-center justify-center size-full">
        <div className="content-stretch flex gap-[20px] items-center justify-center px-[302px] relative size-full">
          <div className="[word-break:break-word] flex flex-col font-['LXGW_Neo_ZhiSong_Screen:Regular',sans-serif] justify-center leading-[0] not-italic relative shrink-0 text-[0px] text-black whitespace-nowrap">
            <p className="font-['Source_Han_Sans_SC:Medium',sans-serif] text-[10px]">
              <span className="leading-none">
                本报地址：国内　霹雳放映站・
              </span>
              <a
                className="[text-decoration-skip-ink:none] [text-underline-position:from-font] cursor-pointer decoration-from-font decoration-solid leading-none underline"
                href="https://space.bilibili.com/3494350898072545"
                target="_blank"
              >
                <span
                  className="[text-decoration-skip-ink:none] [text-underline-position:from-font] decoration-from-font decoration-solid underline"
                  href="https://space.bilibili.com/3494350898072545"
                  target="_blank"
                >
                  走火放映室
                </span>
              </a>
              <span className="leading-none">{`　国外　优博放映站・`}</span>
              <a
                className="[text-decoration-skip-ink:none] [text-underline-position:from-font] cursor-pointer decoration-from-font decoration-solid leading-none underline"
                href="https://www.youtube.com/@Fulinte1966"
                target="_blank"
              >
                <span
                  className="[text-decoration-skip-ink:none] [text-underline-position:from-font] decoration-from-font decoration-solid underline"
                  href="https://www.youtube.com/@Fulinte1966"
                  target="_blank"
                >
                  弗林特放映室
                </span>
              </a>
            </p>
          </div>
          <div className="flex h-[16px] items-center justify-center relative shrink-0 w-0">
            <div className="flex-none rotate-90">
              <div className="h-0 relative w-[16px]">
                <div className="absolute inset-[-1px_0_0_0]">
                  <svg
                    className="block size-full"
                    fill="none"
                    preserveAspectRatio="none"
                    viewBox="0 0 16 1"
                  >
                    <line
                      id="Line 261"
                      stroke="var(--stroke-0, black)"
                      x2="16"
                      y1="0.5"
                      y2="0.5"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
          <Frame2 />
        </div>
      </div>
    </div>
  );
}

function Frame() {
  return (
    <div
      className="-translate-x-1/2 -translate-y-1/2 absolute content-stretch flex flex-col gap-[6px] items-center justify-center left-1/2 overflow-clip top-[calc(50%+5.5px)] w-[1152px]"
      data-name="Frame"
    >
      <Head />
      <div
        className="h-0 relative shrink-0 w-full"
        data-name="Headline"
      >
        <div className="absolute inset-[-2px_0_0_0]">
          <svg
            className="block size-full"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 1152 2"
          >
            <line
              id="Headline"
              stroke="var(--stroke-0, black)"
              strokeWidth="2"
              x2="1152"
              y1="1"
              y2="1"
            />
          </svg>
        </div>
      </div>
      <Newsletter />
      <div
        className="h-[12px] relative shrink-0 w-full"
        data-name="Midline"
      >
        <svg
          width="100%"
          height="12"
          xmlns="http://www.w3.org/2000/svg"
          className="absolute inset-0"
        >
          <defs>
            <pattern
              id="midlineBarcode"
              x="0"
              y="0"
              width="12"
              height="12"
              patternUnits="userSpaceOnUse"
            >
              {/* BorderFont1 barcode tile: 10×4 centered at (1,4) in 12×12 cell */}
              <g transform="translate(1, 4)">
                <rect
                  fill="black"
                  height="4"
                  width="2"
                  x="2.66666"
                />
                <rect
                  fill="black"
                  height="4"
                  width="2"
                  x="8.00001"
                />
                <rect
                  fill="black"
                  height="4"
                  width="0.666667"
                />
                <rect
                  fill="black"
                  height="4"
                  width="0.666667"
                  x="5.33332"
                />
                <rect
                  fill="black"
                  height="4"
                  width="0.666667"
                  x="1.33335"
                />
                <path
                  d="M6.66673 0H7.3334V4H6.66673V0Z"
                  fill="black"
                />
              </g>
            </pattern>
          </defs>
          <rect
            width="100%"
            height="12"
            fill="url(#midlineBarcode)"
          />
        </svg>
      </div>
      <BookShelf />
      <div
        className="h-0 relative shrink-0 w-full"
        data-name="Bottomline"
      >
        <div className="absolute inset-[-2px_0_0_0]">
          <svg
            className="block size-full"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 1152 2"
          >
            <line
              id="Headline"
              stroke="var(--stroke-0, black)"
              strokeWidth="2"
              x2="1152"
              y1="1"
              y2="1"
            />
          </svg>
        </div>
      </div>
      <Contact />
    </div>
  );
}

export default function Homepage() {
  return (
    <div
      className="bg-white relative size-full"
      data-name="Homepage"
    >
      <Frame />
    </div>
  );
}