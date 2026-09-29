import Overview from "./_home/Overview";
import Prelaunch from "./_home/Prelaunch";
import { HAS_FORECAST } from "@/lib/data";

export default function Home() {
  if (HAS_FORECAST) return <Overview />;
  return <Prelaunch today={new Date().toISOString().slice(0, 10)} />;
}
