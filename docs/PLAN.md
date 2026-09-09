# gway-sound migration plan

## Goal

Make `gway-sound` the single owner of reusable GWAY audio behavior currently split between `gway-lcd-sound` and `gway-jabra-recorder`, without moving LCD display behavior, RFID workflows, or unrelated USB/device-management code.

## Core terminology

`gway-sound` distinguishes two kinds of audio data:

- **sounds** are reusable assets intended to be played repeatedly and addressed by a stable logical name.
- **recordings** are generated captures, normally timestamped and append-only.

This distinction should remain visible in both the Python API and the CLI.

## Canonical storage

Use the filesystem as the initial storage and index mechanism. Do not introduce SQLite, a manifest database, or mandatory metadata sidecars in PR1.

```text
/var/lib/gway/sound/
    sounds/
        alert.wav
        success.wav
        failure.wav
        startup.wav
    recordings/
        2026/
            09/
                09/
                    20260909T054812-0600.wav
```

Reusable sounds are operational data and should normally live outside the Python package so they can be replaced without publishing a new `gway-sound` release. A tiny packaged fallback asset may be added later if there is a concrete need.

Recording paths should be sortable, timestamped, and collision-resistant. The preferred default naming convention is local time with an explicit UTC offset, for example `20260909T054812-0600.wav`.

Future capture implementations may add source/device information or optional metadata sidecars without changing the basic directory convention.

### Sound resolution

A sound reference may be a logical name or an explicit file path. Resolution precedence should be:

1. explicit path
2. site/local configured sound directory, when configuration support is added
3. shared GWAY sound directory (`/var/lib/gway/sound/sounds`)
4. packaged fallback, if one is introduced later

Examples:

```python
resolve("alert")
# -> /var/lib/gway/sound/sounds/alert.wav

resolve("alert.wav")
# -> /var/lib/gway/sound/sounds/alert.wav, if present

resolve("/home/arthe/custom.wav")
# -> /home/arthe/custom.wav
```

## PR1 — basic playback and storage contract

PR1 establishes the smallest useful, hardware-independent public contract for the package. It should define canonical sound/recording locations, sound resolution, enumeration, basic playback, and tests.

### Initial Python API

```python
def resolve(sound: str | Path) -> Path: ...


def path(name: str) -> Path: ...


def sounds() -> list[str]: ...


def play(sound: str | Path, *, wait: bool = True) -> None: ...


def stop() -> None: ...
```

Avoid exposing a function named `list`, since it shadows the Python builtin. Use `sounds()` instead.

PR1 should also define the recording-path convention and may expose a path generator such as:

```python
recording.path()
```

The path helper does **not** imply recording/capture support in PR1. It only establishes where future captures belong and how their filenames are generated.

### Initial CLI surface

The CLI should mirror the Python concepts cleanly:

```bash
gway sound play alert
gway sound play /tmp/test.wav
gway sound stop
gway sound sounds
gway sound path alert
```

Later capture work can naturally extend this with `gway sound record` and `gway sound recordings` without changing the PR1 terminology.

### Explicit PR1 exclusions

Do not add the following in PR1:

- capture/recording implementation
- volume control
- looping
- playback-device selection
- Jabra-specific handling
- noise monitoring
- GPIO mute controls
- radio/media helpers
- Piper/TTS
- a database or manifest index

These features should not force a backend abstraction before the requirements from the migrated code are understood.

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

2. **PR1: playback/storage contract**
   - establish canonical `sounds` and `recordings` storage locations
   - implement logical-name/path resolution and sound enumeration
   - implement basic `play` and `stop` behavior
   - expose recording path generation without implementing capture
   - add hardware-independent tests for resolution, storage paths, and playback command behavior
   - keep backend-specific and advanced playback features out of scope

3. **Capture/noise extraction**
   - copy recorder, archive, noise-watch, alarm-toggle, and related tests/docs from `gway-jabra-recorder`
   - separate generic ALSA/PipeWire device selection from Jabra defaults
   - make device identifiers configurable rather than embedding host-specific values
   - use the recording storage/path contract established in PR1

4. **Playback feature extraction**
   - migrate event-sound polling, hotplug playback, compatibility wrappers, GPIO mute, and radio/media helpers from `gway-lcd-sound`
   - preserve legacy command names as delegating wrappers where needed
   - verify LCD services no longer own or lock audio resources unnecessarily

5. **Speech extraction**
   - move Piper daemon and `say-piper`
   - expose a generic TTS command/API while retaining compatibility wrappers

6. **Service consolidation**
   - normalize systemd unit names under `gway-sound`
   - define ownership of playback vs capture processes and restart policy
   - migrate boot-stagger handling only where startup ordering still requires it
   - ensure service units do not require LCD or RFID projects to be installed

7. **Field migration**
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
