// The public file contract, docs/engine-design.md §7. A writer may add fields; the site reads only these.

export type Band = { p10: number; p50: number; p90: number };
export type Party = "D" | "R" | "I";

export type RaceMeta = {
  state: string;
  office: "senate" | "house";
  district: string | number | null;
  special: boolean;
  rcv: boolean;
  candidates: { left: string; right: string };
  left_party: Party;
  incumbent_party: Party;
  status: string;
  tier: "simulate" | "watch" | "statistics";
};

export type Mover = { event_id: string; card: string; delta: number };

export type RaceForecast = {
  p_dem_win: number;
  margin: Band;
  stats_only: { p_dem_win: number; margin: Band };
  left_party: Party;
  benchmarks: { poll_avg: number | null; market: number | null; cook: string | null };
  movers: Mover[];
  news: {
    effect: number;
    switching: number;
    turnout: number;
    if_weaker: { p_dem_win: number };
    if_stronger: { p_dem_win: number };
  };
  today?: { p_dem_win: number; margin: Band; stats_only?: { p_dem_win: number; margin: Band } };
};

export type Control = { p_r_50plus: number; p_d_caucus_51: number; p_independents_decide: number };
export type Seats = { mean: number; p10: number; p50: number; p90: number; dist: Record<string, number> };

export type Forecast = {
  date: string;
  run_id: string;
  schema: number;
  draws: number;
  snapshot?: string;
  sample?: boolean;
  races: Record<string, RaceForecast>;
  senate: Control & {
    seats: { R: Seats; D: Seats; I: Seats };
    not_up: { R: number; D: number; I: number };
    stats_only: Control;
    benchmarks: { market?: number | null };
    news: { if_weaker: number; if_stronger: number };
    today?: Control & { stats_only?: Control };
  };
  house: null | { p_d_majority: number };
};

export type Draws = { races: Record<string, number[]> };

export type History = {
  races: Record<string, { date: string; p_dem_win: number; p50: number }[]>;
  senate: { date: string; p_r_50plus: number }[];
};
