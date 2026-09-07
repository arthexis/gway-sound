# gway-sound migration plan

## Goal

Make `gway-sound` the single owner of reusable GWAY audio behavior currently split between `gway-lcd-sound` and `gway-jabra-recorder`, without moving LCD display behavior, RFID workflows, or unrelated USB/device-management code.

## Source inventory

### From `gway-lcd-sound`

Move the sound-only surface:

- event-sound polling and event-triggered playback
- hotplug sound handling and its udev/systemd integration
- generic sound playback helpers (`sound.sh` / sound command wrappers)
- radio/media playback helpers such as `radio-play`
- GPIO sound mute/toggle helpers
- GPIO-generated audio alerts such as the Imperial March helper
- archived local audio shortcuts and their man pages where still useful
- non-secret event-sound environment templates
- unit tests covering sound behavior without requiring physical audio hardware

Do **not** move:

- LCD rotation, LCD summaries, LCD lockfile runner, node/LCD display services
- LCD environment templates or LCD-specific systemd units

After migration, `gway-lcd-sound` should either become LCD-only (and be renamed/retired separately) or keep temporary compatibility wrappers that delegate sound commands to `gway-sound`.

### From `gway-jabra-recorder`

Move the reusable audio surface:

- rolling audio recorder
- recording archive accounting / recorded-time helper
- archive listening helper
- noise sampling / noise watch logic
- optional noise alarm toggle and playback hook
- Piper TTS daemon and `say-piper`
- recorder/noise/Piper user systemd units
- non-secret recording environment template
- boot-stagger helper where still required by the audio services
- man pages, operating notes, and hardware-independent tests for the above

Keep outside `gway-sound`:

- RFID-triggered recorder launchers and card/kiosk policy (`gway-ap-kiosk`)
- generic USB discovery or charger probing (`gway-field-usb`)
- Jabra-only naming where the behavior is actually generic; retain aliases only for compatibility

## Target structure

```text
src/gway_sound/          reusable Python modules
scripts/gway/            thin executable wrappers where shell/CLI compatibility matters
config/systemd/gway/     sound service units
config/templates/        redacted environment templates
config/udev/rules.d/     sound-related hotplug rules
docs/man/man1/           command man pages
docs/operations/         deployment and migration notes
tests/                   hardware-independent unit tests
```

Prefer generic names (`sound-*`, `audio-*`, `noise-*`, `record-*`, `tts-*`) in new code. Existing `jabra-*` and legacy sound command names can remain as wrappers during the transition so deployed field nodes do not need an atomic cut-over.

## Migration phases

1. **Baseline repository**
   - create an installable `gway-sound` Python package
   - enable `ci-base@v1`
   - keep the initial package hardware-independent so CI can run on GitHub-hosted runners

2. **Playback extraction**
   - copy sound-only scripts, tests, systemd units, udev rules, templates, and docs from `gway-lcd-sound`
   - split shared playback code from command wrappers
   - preserve legacy command names as delegating wrappers
   - verify LCD services no longer own or lock audio resources unnecessarily

3. **Capture/noise extraction**
   - copy recorder, archive, noise-watch, alarm-toggle, and related tests/docs from `gway-jabra-recorder`
   - separate generic ALSA/PipeWire device selection from Jabra defaults
   - make device identifiers configurable rather than embedding host-specific values

4. **Speech extraction**
   - move Piper daemon and `say-piper`
   - expose a generic TTS command/API while retaining compatibility wrappers

5. **Service consolidation**
   - normalize systemd unit names under `gway-sound`
   - define ownership of playback vs capture processes and restart policy
   - migrate boot-stagger handling only where startup ordering still requires it
   - ensure service units do not require LCD or RFID projects to be installed

6. **Field migration**
   - install `gway-sound` beside the old projects on a test GWAY node
   - stop legacy sound/recorder services before enabling replacement units to avoid competing for the same audio device
   - validate playback, mute, hotplug alerts, recording, archive inspection, noise watch, alarm mode, and TTS
   - switch dependent projects to call `gway-sound`
   - remove compatibility wrappers only after deployed nodes no longer reference them

## CI policy

`gway-sound` consumes `arthexis/ci-base/.github/workflows/consumer-ci.yml@v1` and should keep all default hardware-independent checks enabled:

- Ruff lint
- Ruff format check
- pytest on Python 3.11-3.14
- wheel and sdist build
- clean wheel installation and `pip check`

Hardware/service validation remains repository-specific and should be added as non-hardware checks where possible, for example:

```bash
bash -n scripts/gway/*
python -m py_compile src/gway_sound/*.py scripts/gway/*.py
systemd-analyze verify config/systemd/gway/**/*.service config/systemd/gway/**/*.timer
git diff --check
```

Physical microphone, speaker, GPIO, udev, ALSA/PipeWire, and Piper model tests should remain explicit field/integration checks rather than blockers in generic CI.

## Completion criteria

The migration is complete when:

- `gway-sound` owns all reusable playback, capture, noise-monitoring, and TTS code
- `gway-lcd-sound` contains no substantive sound implementation
- `gway-jabra-recorder` contains no substantive generic audio implementation
- compatibility entry points delegate to `gway-sound` or have been retired
- deployed services do not compete for the same playback/capture devices
- `ci-base@v1` and repository-specific static checks pass
