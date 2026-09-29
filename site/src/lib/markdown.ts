// A small Markdown subset for our own trusted files (methods.md, Lab notes): ## / ### headings, paragraphs, - and 1.
// lists, **bold**, *italic*, `code`, [links](url). Anything else renders as text.

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function inline(s: string) {
  return esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, t, u) => {
      const ext = /^https?:/.test(u);
      return `<a href="${u}"${ext ? ' rel="noopener" target="_blank"' : ""}>${t}</a>`;
    });
}

export function slugify(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function toHtml(md: string) {
  const out: string[] = [];
  let list: "ul" | "ol" | null = null;
  let para: string[] = [];
  const flushPara = () => {
    if (para.length) out.push(`<p>${inline(para.join(" "))}</p>`);
    para = [];
  };
  const closeList = () => {
    if (list) out.push(`</${list}>`);
    list = null;
  };
  for (const raw of md.replace(/\r/g, "").split("\n")) {
    const line = raw.trimEnd();
    const h = /^(#{2,3})\s+(.*)$/.exec(line);
    const ul = /^\s*-\s+(.*)$/.exec(line);
    const ol = /^\s*\d+\.\s+(.*)$/.exec(line);
    if (h) {
      flushPara(); closeList();
      const tag = h[1].length === 2 ? "h2" : "h3";
      out.push(`<${tag} id="${slugify(h[2])}">${inline(h[2])}</${tag}>`);
    } else if (ul || ol) {
      flushPara();
      const kind = ul ? "ul" : "ol";
      if (list !== kind) { closeList(); out.push(`<${kind}>`); list = kind; }
      out.push(`<li>${inline((ul ?? ol)![1])}</li>`);
    } else if (!line.trim()) {
      flushPara(); closeList();
    } else if (list && /^\s{2,}\S/.test(raw)) {
      out[out.length - 1] = out[out.length - 1].replace(/<\/li>$/, ` ${inline(line.trim())}</li>`);
    } else {
      closeList();
      para.push(line.trim());
    }
  }
  flushPara(); closeList();
  return out.join("\n");
}

export function headings(md: string) {
  return [...md.matchAll(/^##\s+(.*)$/gm)].map((m) => ({ id: slugify(m[1]), text: m[1] }));
}
