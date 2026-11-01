# Agent guidance

`pia-tools` contains shell hooks and systemd packaging for automating a PIA OpenVPN connection.

## Development

- Check changed shell scripts with `bash -n <files>` and use `shellcheck` when available.
- Review package metadata and service templates together when changing installation behavior.
- Do not run setup, alter system services, or use real VPN account credentials while validating changes.
- Load the `shell` skill before changing shell code.

## CI

- Before changing CI, inspect the current guidance in `pschmitt/ci-workflows`. Pin shared reusable workflow and action references to `@main`.
