// Starts the simlab workflows on time. GitHub fires this repository's own schedules only every 5-9 hours (28-29 Sep
// 2026), but it runs a workflow at once when asked through its API (workflow_dispatch). Cloudflare's cron triggers
// call this at the times below. GH_TOKEN (a Worker secret) is a fine-grained GitHub token that can only run Actions
// on Matteomio16/simlab.
const REPO = "Matteomio16/simlab";
const WORKFLOWS = {
  "*/15 * * * *": ["news.yml", {}],
  "7 */3 * * *": ["snapshot.yml", {}],
  "47 9 * * *": ["daily.yml", { scheduled: "true" }], // obeys PIPELINE_ON and runs once a day
};

export default {
  async scheduled(event, env) {
    const job = WORKFLOWS[event.cron];
    if (!job) return;
    const [workflow, inputs] = job;
    const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "simlab-cron",
      },
      body: JSON.stringify({ ref: "main", inputs }),
    });
    if (r.status !== 204) console.log(`${workflow}: HTTP ${r.status}`);
  },
};
