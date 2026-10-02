# Exit codes

The `bitbucket` CLI keeps data on stdout and diagnostics on stderr. Exit codes
are a stable contract.

| Code | Meaning             | What the agent does                                                      |
| ---- | ------------------- | ------------------------------------------------------------------------ |
| 0    | Success             | Continue.                                                                |
| 1    | Unexpected failure  | Report stderr to the user; retry with `-v` once if useful.               |
| 2    | Invalid usage       | Fix the arguments (check `--help`); global options go first.             |
| 3    | Configuration error | No credential or workspace: run `config list`, ask the user to fix it.   |
| 4    | Authentication      | Ask the user to run `bitbucket auth login`; then stop.                   |
| 5    | Forbidden           | The credential lacks permission; report it, do not retry.                |
| 6    | Not found           | List candidates (`repo list`, `pr list`) and ask the user.               |
| 7    | Validation failure  | Correct the rejected field named in stderr (400, 409 and 422 land here). |
| 8    | Rate limited        | Wait, then retry once; do not loop.                                      |
| 9    | Unavailable         | Bitbucket or the network is down; report it and retry later.             |
