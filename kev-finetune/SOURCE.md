Copied from https://github.com/jaredpalmer/kev (Apache-2.0, see LICENSE), `skills/kev-finetune` at commit
5920c5fe4ca8e0970ed4209ac2c9b8e18bea5109 (26 Sep 2026). The Modal image still installs Kev itself at the `KEV_REF`
pinned in `scripts/kev_modal.py`.

Changes made for simlab (27 Sep 2026), all in `scripts/kev_modal.py`: the serving settings `KEV_SERVE_MAX_CONTAINERS`
(default 1), `KEV_SERVE_IDLE_S` (default 60 s; upstream 300) and `KEV_SERVE_TEMPERATURE` (empty = the checkpoint's
fitted temperature; 1.0 = raw probabilities, which our soft-target runs need).

Training data: `../data/kev/<run>/`, built by `python -m simlab.kevdata`. Run commands from this folder, e.g.
`python -m modal run scripts/kev_modal.py::train --data ../data/kev/ces-v1 --name ces-v1 --timeout 3000`; reports land
in `runs/<name>/`. Modal console logs contain workspace details, so they are git-ignored (`*.log` here); copies go to
the private data repo.
