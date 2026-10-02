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
