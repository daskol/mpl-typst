# Changelog

## [Unreleased]

[unreleased]: https://github.com/daskol/mpl-typst/compare/v0.3.0...HEAD

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.3.0] - 2026-05-11

[0.3.0]: https://github.com/daskol/mpl-typst/compare/v0.2.1...v0.3.0

### Added

- Add basic text color support, including `twinx` y-axis labels (#29).
- Apply bounding box clipping to paths and meshes (#33).

### Changed

- Update the release pipeline to publish from GitHub Releases and PyPI Trusted
  Publishing (#37).

### Fixed

- Fix rendering of hatched boxes (#35).
- Anchor generated Typst `place()` calls with `top + left` for stable placement
  (#36).
- Use SPDX-style MIT license metadata to avoid packaging warnings (#37).

## [0.2.1] - 2024-05-17

[0.2.1]: https://github.com/daskol/mpl-typst/compare/v0.2.0...v0.2.1

### Fixed

- Pin minimal version of `matplotlib` (#25).
