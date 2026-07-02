import { siteConfig } from "./site";

const UAPIS_BASE = "https://uapis.cn/api/v1";

function uapiAuthHeaders(): Record<string, string> {
  const key = import.meta.env.UAPI_KEY ?? process.env.UAPI_KEY;
  if (!key) return {};
  return { Authorization: `Bearer ${key}` };
}

export interface CalendarStatus {
  dateLabel: string;
  weekdayLabel: string;
  lunarLabel?: string;
}

export interface WeatherForecastDay {
  date: string;
  temp_max?: number;
  temp_min?: number;
  weather_day?: string;
  weather_night?: string;
  wind_dir_day?: string;
  wind_dir_night?: string;
  wind_scale_day?: string;
  wind_scale_night?: string;
}

export interface WeatherStatus {
  city: string;
  weather: string;
  temperature?: number;
  wind_direction?: string;
  wind_power?: string;
  wind?: string;
  humidity?: number;
  temp_max?: number;
  temp_min?: number;
  forecast?: WeatherForecastDay[];
}

interface LunartimeResponse {
  weekday_cn?: string;
  lunar_year_cn?: string;
  lunar_month_cn?: string;
  lunar_day_cn?: string;
  ganzhi_year?: string;
}

interface WeatherResponse {
  city?: string;
  weather?: string;
  temperature?: number;
  wind_direction?: string;
  wind_power?: string;
  humidity?: number;
  temp_max?: number;
  temp_min?: number;
  forecast?: WeatherForecastDay[];
}

function uapiFetch(pathname: string, params?: URLSearchParams): Promise<Response> {
  const url = new URL(`${UAPIS_BASE}${pathname}`);
  if (params) {
    for (const [key, value] of params) {
      url.searchParams.set(key, value);
    }
  }
  return fetch(url, {
    headers: uapiAuthHeaders(),
    signal: AbortSignal.timeout(3500),
  });
}

function chinaToday(): Date {
  const formatted = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  return new Date(`${formatted}T00:00:00+08:00`);
}

function formatDateLabel(date: Date): string {
  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;
  return `${year} 年 ${month} 月 ${day} 日`;
}

function formatWeekdayLabel(date: Date): string {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    weekday: "long",
  }).format(date);
}

export async function getCalendarStatus(): Promise<CalendarStatus> {
  const today = chinaToday();
  const ts = Math.floor(today.getTime() / 1000).toString();

  try {
    const params = new URLSearchParams();
    params.set("ts", ts);
    params.set("timezone", "Asia/Shanghai");

    const response = await uapiFetch("/misc/lunartime", params);
    if (!response.ok) {
      throw new Error(`uapis lunartime ${response.status}`);
    }

    const data = (await response.json()) as LunartimeResponse;
    if (!data.weekday_cn) {
      throw new Error("uapis lunartime missing weekday_cn");
    }

    return {
      dateLabel: formatDateLabel(today),
      weekdayLabel: data.weekday_cn,
      lunarLabel:
        data.ganzhi_year && data.lunar_month_cn && data.lunar_day_cn
          ? `农历${data.ganzhi_year}年${data.lunar_month_cn}${data.lunar_day_cn}`
          : undefined,
    };
  } catch {
    return {
      dateLabel: formatDateLabel(today),
      weekdayLabel: formatWeekdayLabel(today),
    };
  }
}

export async function getWeatherStatus(): Promise<WeatherStatus | undefined> {
  try {
    const params = new URLSearchParams();
    params.set("city", siteConfig.weatherCity);
    params.set("lang", "zh");
    params.set("forecast", "true");

    const response = await uapiFetch("/misc/weather", params);
    if (!response.ok) {
      throw new Error(`uapis weather ${response.status}`);
    }

    const data = (await response.json()) as WeatherResponse;
    if (!data.city || !data.weather) {
      throw new Error("uapis weather missing city/weather");
    }

    return {
      city: data.city,
      weather: data.weather,
      temperature: data.temperature,
      wind_direction: data.wind_direction,
      wind_power: data.wind_power,
      wind:
        data.wind_direction || data.wind_power
          ? `${data.wind_direction ?? ""}${data.wind_power ?? ""}`
          : undefined,
      humidity: data.humidity,
      temp_max: data.temp_max,
      temp_min: data.temp_min,
      forecast: data.forecast,
    };
  } catch {
    return undefined;
  }
}
