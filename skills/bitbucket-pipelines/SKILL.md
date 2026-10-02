---
name: bitbucket-pipelines
description: >-
  Run and inspect Bitbucket Pipelines with the bitbucket CLI: start, stop and
  list pipelines, read step logs and test reports, manage pipeline variables,
  schedules, caches, runners and known hosts, and work with deployment
  environments and deployments. Use when the user says "run the pipeline",
  "trigger a build", "why did the pipeline fail", "show the build log", "stop
  the pipeline", "add a pipeline variable", "schedule a pipeline", or asks
  about environments and deployments.
license: MIT
compatibility: Requires the bitbucket CLI (bitbucket-unofficial-cli, Python 3.14+) and a logged-in Bitbucket credential
allowed-tools: Bash Read AskUserQuestion
---

# Bitbucket pipelines

Drive `bitbucket pipeline`, `environment` and `deployment`. For pull requests
use the `bitbucket-pull-requests` skill; for everything else, `bitbucket-cli`.

## Rules

- Global options (`-p`, `-w`, `-o`, `-v`) MUST come before the subcommand:
  `bitbucket -o json pipeline list -r my-repo`.
- MUST pass `-o json` (or `-o id`) whenever the output is parsed. Data is on
  stdout; notices and the next-page cursor are on stderr.
- Commands take `--repo/-r SLUG` (or `BITBUCKET_REPOSITORY`). Variables, caches,
  runners and similar settings also exist without `--repo` for the workspace.
- `pipeline log PIPELINE STEP` prints raw text, optionally a byte range with
  `--start` and `--end`; it is not JSON.
- Secrets MUST NOT be passed as arguments or printed. A variable value comes
  from a hidden prompt or `--stdin`. To run with variables, pass the name of
  an environment variable: `--variable-env NAME`, or `--secured-variable-env
  NAME` for a secured one.
- Fields without a flag go through `--from-file FILE` (or `-`) as JSON.

## Instructions

1. MUST run `bitbucket --version`. If it is missing, recommend `uv tool
   install bitbucket-unofficial-cli` or `pipx install bitbucket-unofficial-cli`
   and stop.
2. MUST run `bitbucket -o json auth status`. On exit code 3 or 4, tell the
   user to run `bitbucket auth login` and stop.
3. Choose the workflow:

   | Goal           | Command                                                                                                    |
   | -------------- | ---------------------------------------------------------------------------------------------------------- |
   | List runs      | `bitbucket -o json pipeline list -r REPO [--branch B] [--status S] [--sort -created_on] [--limit N]`       |
   | Show a run     | `bitbucket -o json pipeline get PIPELINE -r REPO`                                                          |
   | Start a run    | `bitbucket pipeline run -r REPO (--branch B / --tag T / --commit H) [--custom NAME] [--variable-env NAME]` |
   | Stop a run     | `bitbucket pipeline stop PIPELINE -r REPO`                                                                 |
   | Steps and logs | `pipeline steps PIPELINE`, `pipeline step PIPELINE STEP`, `pipeline log PIPELINE STEP`                     |
   | Test reports   | `pipeline tests`, `pipeline test-cases`, `pipeline test-case-reasons`                                      |
   | Variables      | `pipeline variable list/get/create/update/delete`                                                          |
   | Schedules      | `pipeline schedule list/get/create/update/delete/executions`                                               |
   | Other settings | `pipeline config get/update/build-number`, `known-host`, `ssh-key`, `cache`, `runner`                      |
   | Environments   | `environment list/get/create/update/delete`, `environment variable ...`                                    |
   | Deployments    | `deployment list/get`                                                                                      |

4. To find out why a run failed: `pipeline get`, then `pipeline steps` to see
   the failing step, then `pipeline log PIPELINE STEP`, and `pipeline tests`
   when the step produced a test report. Summarize the error; do not dump the
   whole log.
5. After `pipeline run`, check progress with `pipeline get`. MUST NOT poll in
   a tight loop; check a few times with a pause, then report the state.
6. MUST ask the user with `AskUserQuestion` before `pipeline run` on a
   shared branch such as the main one, before `pipeline stop`, and before any
   `delete`; pass `--yes` to a `delete` only after that.
7. On a non-zero exit, follow [exit-codes.md](references/exit-codes.md).

Run `bitbucket pipeline <command> --help` for flags not listed here.
