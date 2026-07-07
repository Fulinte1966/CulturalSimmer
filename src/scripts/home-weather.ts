const weatherBox = document.querySelector<HTMLElement>(".fm-weather[data-weather-city]");
if (weatherBox) {
  const setField = (field: string, value?: string | number) => {
    if (value === undefined || value === null || value === "") return;
    const target = weatherBox.querySelector<HTMLElement>(`[data-weather-field="${field}"]`);
    if (target) target.textContent = String(value);
  };

  const setScale = (field: string, value?: string | number) => {
    if (value === undefined || value === null || value === "") return;
    const target = weatherBox.querySelector<HTMLElement>(`[data-weather-field="${field}"]`);
    if (!target) return;
    const text = String(value);
    const match = text.match(/^(\d+(?:\.\d+)?)(.*)$/);
    const numberTarget = target.querySelector<HTMLElement>("[data-weather-number]");
    const unitTarget = target.querySelector<HTMLElement>("[data-weather-unit]");
    if (!numberTarget || !unitTarget || !match) {
      target.textContent = text;
      return;
    }
    numberTarget.textContent = match[1];
    unitTarget.textContent = match[2] || "级";
  };

  const setForecast = (index: number, day?: string, weather?: string) => {
    const dayTarget = weatherBox.querySelector<HTMLElement>(`[data-weather-day="${index}"]`);
    const weatherTarget = weatherBox.querySelector<HTMLElement>(`[data-weather-forecast="${index}"]`);
    if (dayTarget && day) {
      const match = String(day).match(/^(.+?)(日)$/);
      const numberTarget = dayTarget.querySelector<HTMLElement>("[data-weather-day-number]");
      const unitTarget = dayTarget.querySelector<HTMLElement>("[data-weather-day-unit]");
      if (numberTarget && unitTarget && match) {
        numberTarget.textContent = match[1];
        unitTarget.textContent = match[2];
      } else {
        dayTarget.textContent = day;
      }
    }
    if (weatherTarget && weather) weatherTarget.textContent = weather;
  };

  const updateWeather = async () => {
    const city = weatherBox.dataset.weatherCity;
    if (!city) return;

    const url = new URL("https://uapis.cn/api/v1/misc/weather");
    url.searchParams.set("city", city);
    url.searchParams.set("lang", "zh");
    url.searchParams.set("forecast", "true");

    try {
      const response = await fetch(url);
      if (!response.ok) return;
      const data = await response.json();
      if (!data.city || !data.weather) return;

      const current = Array.isArray(data.forecast) ? data.forecast[0] : undefined;
      setField("city", `${data.city}地区`);
      setField("dayWeather", current?.weather_day ?? data.weather);
      setField("nightWeather", current?.weather_night ?? data.weather);
      setField("dayWindDir", current?.wind_dir_day ?? data.wind_direction);
      setScale("dayWindScale", current?.wind_scale_day ?? data.wind_power);
      setField("nightWindDir", current?.wind_dir_night ?? data.wind_direction);
      setScale("nightWindScale", current?.wind_scale_night ?? data.wind_power);
      setField("tempMax", current?.temp_max ?? data.temp_max ?? data.temperature);
      setField("tempMin", current?.temp_min ?? data.temp_min ?? data.temperature);

      for (const [index, day] of (data.forecast ?? []).slice(1, 4).entries()) {
        const date = day.date ? new Date(`${day.date}T00:00:00+08:00`) : undefined;
        const dayLabel = date && !Number.isNaN(date.getTime()) ? `${date.getDate()}日` : undefined;
        setForecast(index, dayLabel, day.weather_day ?? day.weather_night);
      }
    } catch {
      // Keep the static fallback if the public weather API is rate-limited.
    }
  };

  updateWeather();
}
