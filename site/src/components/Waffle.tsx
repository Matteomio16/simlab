// 100 squares, one per simulated election in a hundred: who controls the Senate.
export default function Waffle({ r, d, i }: { r: number; d: number; i: number }) {
  const other = Math.max(0, 100 - r - d - i);
  const cells = [
    ...Array(r).fill("var(--rep)"),
    ...Array(i).fill("var(--ind)"),
    ...Array(other).fill("var(--rule)"),
    ...Array(d).fill("var(--dem)"),
  ].slice(0, 100);
  return (
    <div className="grid grid-cols-[repeat(25,minmax(0,1fr))] gap-[3px]" role="img"
      aria-label={`Of 100 simulated elections, Republicans hold the Senate in ${r}, Democrats reach 51 in ${d}, independents decide in ${i}.`}>
      {cells.map((c, k) => (
        <span key={k} className="waffle-cell aspect-square" style={{ background: c, ["--i" as string]: k }} />
      ))}
    </div>
  );
}
