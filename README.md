# gway-sound

Shared sound capture, playback, alerting, and speech helpers for GWAY field nodes.

This repository is being populated by extracting sound-owned functionality from `gway-lcd-sound` and `gway-jabra-recorder`. LCD display behavior stays in the LCD project; Jabra-specific device policy may remain as a thin compatibility layer, while reusable audio behavior moves here.

See [`docs/PLAN.md`](docs/PLAN.md) for the migration plan.

## Core commands

Reusable playback and recording are exposed through the Python adapter:

```bash
gway sound play alert
gway sound sounds
gway sound sources
gway sound record --seconds 5
gway sound record --source SOURCE --name inspection
gway sound recordings
gway sound stop
```

`gway sound stop` is intentionally global: it stops both active playback and active recording started by `gway-sound`.

Recordings use the canonical archive under `/var/lib/gway/sound/recordings`. Omitting `--seconds` starts a background recording that continues until `gway sound stop` is called.

## CI

The repository consumes the shared Arthexis Python CI baseline from `arthexis/ci-base@v1`. The baseline runs Ruff lint/format checks, pytest across supported Python versions, package builds, and clean-install validation.

