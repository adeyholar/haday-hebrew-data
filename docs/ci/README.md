# Workflows waiting to be installed

These two files are the intended `.github/workflows/build.yml` and `.github/workflows/release.yml`.
They are kept here because the token Dev Desk pushes with has no `workflow` scope, and GitHub refuses a
workflow change from such a token. They are not active in this folder.

To install them, someone with a workflow-scoped token (or the GitHub web editor) copies them into place:

    cp docs/ci/build.yml docs/ci/release.yml .github/workflows/

`build.yml` adds Node 22, the full-corpus canon parity step, and the two-build reproducibility check.
`release.yml` builds and publishes a release when a `v<version>` tag is pushed on `main`.
Until then, releases are made by hand with `scripts/package.sh`, which writes the same assets and `SHA256SUMS`.
