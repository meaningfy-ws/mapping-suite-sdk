# Re-shape record: SonarQube Cloud on the free plan (2026-11-08)

> Secondary input, preserved. Logged EPIC-level change to DEC-7.

- Developer: "sonar was downgraded to free version, adapt accordingly".
- Observed: the CI `SonarCloud Scan` step fails with HTTP 403 (`SONAR_TOKEN` rejected) on every
  run since 2026-03-18; the required `SonarCloud Code Analysis` check never reports.
- Decision: no Sonar in CI; the free plan analyses this public repo via Automatic Analysis
  (`.sonarcloud.properties`); Codecov owns coverage. Applied on `develop` by PR "fix(ci): drop the
  SonarCloud CI scan" ahead of this change; this change keeps it that way.
