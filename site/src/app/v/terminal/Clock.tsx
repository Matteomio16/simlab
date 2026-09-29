"use client";

import { useEffect, useState } from "react";

export default function Clock() {
  const [t, setT] = useState("");
  useEffect(() => {
    const tick = () => setT(new Date().toISOString().slice(0, 19).replace("T", " ") + "Z");
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="tabular-nums">{t || "—"}</span>;
}
