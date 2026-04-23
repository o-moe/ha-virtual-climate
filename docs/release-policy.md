# Release Policy

`ha-virtual-climate` uses a lightweight semantic versioning policy.

## Stable releases

- Stable releases are tagged as `vX.Y.Z`.
- Stable releases are created manually from `main`.
- A stable release represents a state that is suitable for ordinary reuse in
  Home Assistant test instances.

## Alpha pre-releases

- Alpha pre-releases are tagged as `vX.Y.Z-alpha.N`.
- Alpha pre-releases are created manually from a selected ref.
- They are intended for fast iteration while implementing or validating new
  testing features.

## Beta pre-releases

- Beta pre-releases are tagged as `vX.Y.Z-beta.N`.
- Beta pre-releases are created automatically from `main`.
- A beta pre-release is skipped when a stable release for the same version
  already exists.

## Version source of truth

- `custom_components/virtual_climate/manifest.json` and
  `.github/release-plan.json` must agree on the target version.
- The target version identifies the next intended stable release line.

## Current release line

- The repository currently targets stable version `0.1.0`.
- Pre-releases in the current line are for the initial bootstrap milestone.
