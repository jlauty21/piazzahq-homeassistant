# Piazza HQ for Home Assistant

A custom Home Assistant integration for [Piazza HQ](https://piazzahq.com) —
the always-on calendar/family-hub display for Raspberry Pi, Windows, and
Docker. Lets Home Assistant turn a Piazza HQ screen's TV/monitor on or off,
and switch a display to a saved layout (which also switches its light/dark
theme), from any automation.

This is a third way to connect Home Assistant to Piazza HQ, alongside the
`rest_command:` YAML door and the MQTT Discovery door already built into
Piazza HQ itself (Settings → Home Assistant Control). All three reach the
exact same two underlying actions — pick whichever fits your setup. **Don't
run this integration and the MQTT door at the same time for the same
device** — you'd get duplicate entities for the same screens and displays.

## What you get

- One **switch** per screen that has TV/monitor control configured in
  Piazza HQ — power on/off.
- One **select** per display — its options are your saved layouts in Piazza
  HQ; picking one applies that layout (and its theme) to the display.

Both are command-only. Piazza HQ can't reliably report whether a TV is
actually on (most remotes have no "are you on" signal to ask), and there's
no stored record of which saved layout is currently active on a display —
so both entities show up in Home Assistant as **assumed state**, the same
honest limitation the `rest_command:` and MQTT doors already have.

New screens, displays, or saved layouts added in Piazza HQ after setup
appear automatically within a few minutes — no need to reload the
integration by hand.

## Installation

### Via HACS (custom repository)

1. In Home Assistant, open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/jlauty21/piazzahq-homeassistant`, category
   **Integration**.
3. Find "Piazza HQ" in HACS and install it.
4. Restart Home Assistant.

### Manual

Copy `custom_components/piazzahq` into your Home Assistant config's
`custom_components/` folder, then restart Home Assistant.

## Setup

1. In Piazza HQ, go to **Settings → Home Assistant Control** and tap
   **Generate Token**.
2. In Home Assistant, go to **Settings → Devices & Services → Add
   Integration**, search for **Piazza HQ**.
3. Enter the device's IP address (its port defaults to `3000`) and paste in
   the token from step 1.

If you have more than one Piazza HQ device (a host and mirror displays),
add each one as its own integration entry.

## License

MIT — see [LICENSE](LICENSE).
