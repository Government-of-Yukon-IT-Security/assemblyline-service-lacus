# Lacus Service

This service extracts artifacts and captures from potentially malicious URLs.
It uses the [Lacus](https://github.com/ail-project/lacus) tool from the [AIL Project](https://www.ail-project.org/).

## Overview

This service deploys a local docker instance of Lacus and utilizes PyLacus to extract and return artifacts from URLs to
Assembyline.

It was developed as a Proof of Concept (POC) service module for GeekWeek 10.

## Architecture
Lacus is deployed basically as per the official deployment script on the Lacus repo. `supervisord` is used to ensure
all dependent services remain online as expected.

[PyLacus](https://github.com/ail-project/PyLacus) is used to provide an easy upgrade path to

## TODO

- So much
- Add customizable User-Agent and HTTP Proxy
- Optimize Dockerfile (size/performance of Lacus)
- Resolve $SERVICE_TAG issues in service_manifest.yml
- Consider fully implementing LookyLoo to provide additional analysis/artifacts

# Collaborators

- [Government of Yukon/Thomas Dang](https://github.com/litobro)
- [CIRCL/Raphael Vinot](https://github.com/Rafiot)
- [CCCS Assemblyline Team](https://github.com/cybercentrecanada)