from typing import Final

from bitbucket_unofficial_cli.output.renderer import Column

AUTH_STATUS: Final = (
    Column("profile", "Profile"),
    Column("user", "User"),
    Column("kind", "Credential"),
    Column("source", "Source"),
    Column("expiresAt", "Expires"),
    Column("secret", "Secret"),
)

PROFILES: Final = (
    Column("name", "Profile"),
    Column("default", "Default"),
    Column("workspace", "Workspace"),
    Column("displayName", "User"),
)

WORKSPACES: Final = (
    Column("workspace.slug", "Slug"),
    Column("workspace.name", "Name"),
    Column("workspace.is_private", "Private"),
    Column("administrator", "Admin"),
)

WORKSPACE: Final = (
    Column("slug", "Slug"),
    Column("name", "Name"),
    Column("uuid", "UUID"),
    Column("is_private", "Private"),
    Column("created_on", "Created"),
)

USERS: Final = (
    Column("display_name", "Name"),
    Column("nickname", "Nickname"),
    Column("account_id", "Account ID"),
    Column("uuid", "UUID"),
    Column("account_status", "Status"),
)

REPOSITORIES: Final = (
    Column("full_name", "Repository"),
    Column("is_private", "Private"),
    Column("language", "Language"),
    Column("mainbranch.name", "Main branch"),
    Column("updated_on", "Updated"),
)

REPOSITORY: Final = (
    *REPOSITORIES,
    Column("slug", "Slug"),
    Column("uuid", "UUID"),
    Column("description", "Description"),
    Column("scm", "SCM"),
    Column("project.key", "Project"),
    Column("owner.display_name", "Owner"),
    Column("created_on", "Created"),
)

PROJECTS: Final = (
    Column("key", "Key"),
    Column("name", "Name"),
    Column("is_private", "Private"),
    Column("description", "Description"),
    Column("updated_on", "Updated"),
)

PROJECT: Final = (*PROJECTS, Column("uuid", "UUID"), Column("created_on", "Created"))

ACCOUNTS: Final = (
    Column("display_name", "Name"),
    Column("nickname", "Nickname"),
    Column("account_id", "Account ID"),
    Column("uuid", "UUID"),
)

MEMBERS: Final = (
    Column("user.display_name", "Name"),
    Column("user.nickname", "Nickname"),
    Column("user.account_id", "Account ID"),
    Column("permission", "Permission"),
    Column("added_on", "Added"),
    Column("last_accessed", "Last accessed"),
)

REPOSITORY_PERMISSIONS: Final = (
    Column("repository.full_name", "Repository"),
    Column("user.display_name", "User"),
    Column("permission", "Permission"),
)

WEBHOOKS: Final = (
    Column("uuid", "UUID"),
    Column("description", "Description"),
    Column("url", "URL"),
    Column("active", "Active"),
    Column("subject_type", "Subject"),
)

WEBHOOK: Final = (*WEBHOOKS, Column("events", "Events"), Column("created_at", "Created"))

HOOK_EVENTS: Final = (
    Column("event", "Event"),
    Column("category", "Category"),
    Column("label", "Label"),
    Column("description", "Description"),
)

PULL_REQUESTS: Final = (
    Column("id", "ID"),
    Column("title", "Title"),
    Column("state", "State"),
    Column("author.display_name", "Author"),
    Column("source.branch.name", "Source"),
    Column("destination.branch.name", "Destination"),
    Column("updated_on", "Updated"),
)

PULL_REQUEST: Final = (
    *PULL_REQUESTS,
    Column("description", "Description"),
    Column("draft", "Draft"),
    Column("close_source_branch", "Closes source"),
    Column("comment_count", "Comments"),
    Column("task_count", "Tasks"),
    Column("merge_commit.hash", "Merge commit"),
    Column("created_on", "Created"),
)

ACTIVITIES: Final = (
    Column("update.date", "Updated"),
    Column("update.author.display_name", "By"),
    Column("update.state", "State"),
    Column("approval.date", "Approved"),
    Column("approval.user.display_name", "Approved by"),
    Column("changes_requested.user.display_name", "Changes by"),
    Column("comment.user.display_name", "Commenter"),
    Column("comment.content.raw", "Comment"),
)

CHECKS: Final = (
    Column("type", "Check"),
    Column("status", "Status"),
    Column("required", "Required"),
    Column("blocking", "Blocking"),
    Column("message", "Message"),
)

MERGE_TASK: Final = (Column("task_id", "Task"),)

MERGE_STATUS: Final = (
    Column("task_status", "Status"),
    Column("message", "Message"),
    Column("pull_request.id", "Pull request"),
    Column("pull_request.state", "State"),
)

DIFFSTATS: Final = (
    Column("status", "Status"),
    Column("old.path", "Old"),
    Column("new.path", "New"),
    Column("lines_added", "Added"),
    Column("lines_removed", "Removed"),
)

COMMITS: Final = (
    Column("hash", "Hash"),
    Column("date", "Date"),
    Column("author.raw", "Author"),
    Column("message", "Message"),
)

CONFLICTS: Final = (
    Column("path", "Path"),
    Column("scenario", "Scenario"),
    Column("type", "Type"),
    Column("message", "Message"),
)

COMMENTS: Final = (
    Column("id", "ID"),
    Column("user.display_name", "Author"),
    Column("content.raw", "Comment"),
    Column("inline.path", "File"),
    Column("inline.to", "Line"),
    Column("parent.id", "Parent"),
    Column("resolution.user.display_name", "Resolved by"),
    Column("created_on", "Created"),
)

TASKS: Final = (
    Column("id", "ID"),
    Column("state", "State"),
    Column("content.raw", "Task"),
    Column("creator.display_name", "Creator"),
    Column("created_on", "Created"),
)

PULL_REQUEST_STATUSES: Final = (
    Column("key", "Key"),
    Column("name", "Name"),
    Column("state", "State"),
    Column("description", "Description"),
    Column("url", "URL"),
    Column("updated_on", "Updated"),
)

BRANCHES: Final = (
    Column("name", "Branch"),
    Column("target.hash", "Commit"),
    Column("default_merge_strategy", "Merge strategy"),
)

TAGS: Final = (
    Column("name", "Tag"),
    Column("target.hash", "Commit"),
    Column("tagger.display_name", "Tagger"),
    Column("date", "Date"),
    Column("message", "Message"),
)

REFS: Final = (Column("type", "Type"), Column("name", "Name"), Column("target.hash", "Commit"))

COMMIT: Final = (
    *COMMITS,
    Column("committer.raw", "Committer"),
    Column("parents", "Parents"),
)

TREE: Final = (
    Column("path", "Path"),
    Column("type", "Type"),
    Column("size", "Size"),
    Column("commit.hash", "Commit"),
)

FILE_HISTORY: Final = (Column("path", "Path"), Column("commit.hash", "Commit"))

REPORTS: Final = (
    Column("external_id", "ID"),
    Column("title", "Title"),
    Column("reporter", "Reporter"),
    Column("report_type", "Type"),
    Column("result", "Result"),
    Column("updated_on", "Updated"),
)

REPORT: Final = (*REPORTS, Column("details", "Details"), Column("link", "Link"), Column("uuid", "UUID"))

ANNOTATIONS: Final = (
    Column("external_id", "ID"),
    Column("title", "Title"),
    Column("annotation_type", "Type"),
    Column("severity", "Severity"),
    Column("result", "Result"),
    Column("path", "Path"),
    Column("line", "Line"),
    Column("summary", "Summary"),
)

DOWNLOADS: Final = (
    Column("name", "File"),
    Column("size", "Size"),
    Column("downloads", "Downloads"),
    Column("user.display_name", "Uploaded by"),
    Column("created_on", "Created"),
)

BRANCH_RESTRICTIONS: Final = (
    Column("id", "ID"),
    Column("kind", "Kind"),
    Column("branch_match_kind", "Match"),
    Column("pattern", "Pattern"),
    Column("branch_type", "Branch type"),
    Column("value", "Value"),
)

BRANCHING_MODEL: Final = (
    Column("development.name", "Development"),
    Column("development.use_mainbranch", "Uses main"),
    Column("production.name", "Production"),
    Column("production.use_mainbranch", "Uses main"),
)

BRANCHING_SETTINGS: Final = (
    Column("development.name", "Development"),
    Column("development.enabled", "Enabled"),
    Column("production.name", "Production"),
    Column("production.enabled", "Enabled"),
)

DEFAULT_REVIEWERS: Final = (
    Column("display_name", "Name"),
    Column("nickname", "Nickname"),
    Column("account_id", "Account ID"),
    Column("reviewer_type", "Type"),
)

PROJECT_DEFAULT_REVIEWERS: Final = (
    Column("user.display_name", "Name"),
    Column("user.nickname", "Nickname"),
    Column("user.account_id", "Account ID"),
    Column("reviewer_type", "Type"),
)

DEPLOY_KEYS: Final = (
    Column("id", "ID"),
    Column("label", "Label"),
    Column("key", "Key"),
    Column("created_on", "Created"),
    Column("last_used", "Last used"),
)

GROUP_PERMISSIONS: Final = (
    Column("group.slug", "Group"),
    Column("group.name", "Name"),
    Column("permission", "Permission"),
)

USER_PERMISSIONS: Final = (
    Column("user.display_name", "Name"),
    Column("user.account_id", "Account ID"),
    Column("permission", "Permission"),
)

OVERRIDE_SETTINGS: Final = (
    Column("override_settings.branching_model", "Branching model"),
    Column("override_settings.branch_restrictions", "Branch restrictions"),
    Column("override_settings.default_merge_strategy", "Merge strategy"),
)

PIPELINES: Final = (
    Column("build_number", "#"),
    Column("uuid", "UUID"),
    Column("state.name", "State"),
    Column("state.result.name", "Result"),
    Column("target.ref_name", "Ref"),
    Column("creator.display_name", "Creator"),
    Column("created_on", "Created"),
    Column("build_seconds_used", "Seconds"),
)

PIPELINE_STEPS: Final = (
    Column("uuid", "UUID"),
    Column("state.name", "State"),
    Column("state.result.name", "Result"),
    Column("image.name", "Image"),
    Column("started_on", "Started"),
    Column("completed_on", "Completed"),
)

PIPELINE_VARIABLES: Final = (
    Column("uuid", "UUID"),
    Column("key", "Key"),
    Column("value", "Value"),
    Column("secured", "Secured"),
)

SCHEDULES: Final = (
    Column("uuid", "UUID"),
    Column("enabled", "Enabled"),
    Column("cron_pattern", "Cron"),
    Column("target.ref_name", "Ref"),
    Column("target.selector.pattern", "Pipeline"),
    Column("updated_on", "Updated"),
)

SCHEDULE_EXECUTIONS: Final = (
    Column("type", "Type"),
    Column("pipeline.build_number", "Build"),
    Column("pipeline.uuid", "Pipeline"),
    Column("error.message", "Error"),
)

KNOWN_HOSTS: Final = (
    Column("uuid", "UUID"),
    Column("hostname", "Host"),
    Column("public_key.key_type", "Key type"),
    Column("public_key.sha256_fingerprint", "SHA-256"),
)

CACHES: Final = (
    Column("uuid", "UUID"),
    Column("name", "Name"),
    Column("path", "Path"),
    Column("file_size_bytes", "Bytes"),
    Column("created_on", "Created"),
)

CACHE_URI: Final = (Column("uri", "URI"),)

RUNNERS: Final = (
    Column("uuid", "UUID"),
    Column("name", "Name"),
    Column("labels", "Labels"),
    Column("state.status", "Status"),
    Column("state.version.version", "Version"),
    Column("created_on", "Created"),
)

SSH_KEY_PAIR: Final = (Column("public_key", "Public key"),)

PIPELINES_CONFIG: Final = (Column("enabled", "Enabled"), Column("repository.full_name", "Repository"))

BUILD_NUMBER: Final = (Column("next", "Next build"),)

ENVIRONMENTS: Final = (Column("uuid", "UUID"), Column("name", "Name"))

DEPLOYMENTS: Final = (
    Column("uuid", "UUID"),
    Column("environment.name", "Environment"),
    Column("state.name", "State"),
    Column("state.status.name", "Status"),
    Column("release.name", "Release"),
    Column("release.commit.hash", "Commit"),
    Column("state.start_date", "Started"),
)

EMAILS: Final = (
    Column("email", "Email"),
    Column("is_primary", "Primary"),
    Column("is_confirmed", "Confirmed"),
)

SSH_KEYS: Final = (
    Column("uuid", "UUID"),
    Column("label", "Label"),
    Column("fingerprint", "Fingerprint"),
    Column("created_on", "Created"),
    Column("last_used", "Last used"),
    Column("expires_on", "Expires"),
)

GPG_KEYS: Final = (
    Column("fingerprint", "Fingerprint"),
    Column("name", "Name"),
    Column("key_id", "Key ID"),
    Column("created_on", "Created"),
    Column("expires_on", "Expires"),
)

CODE_SEARCH: Final = (
    Column("file.path", "Path"),
    Column("content_match_count", "Matches"),
    Column("file.commit.hash", "Commit"),
)

SNIPPETS: Final = (
    Column("id", "ID"),
    Column("title", "Title"),
    Column("is_private", "Private"),
    Column("owner.display_name", "Owner"),
    Column("updated_on", "Updated"),
)

SNIPPET: Final = (*SNIPPETS, Column("scm", "SCM"), Column("created_on", "Created"))
