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
