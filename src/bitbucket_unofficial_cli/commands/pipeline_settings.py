from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.pipeline_config import PipelineBuildNumberUpdate
from bitbucket.models.pipeline_config import PipelineKnownHostCreate
from bitbucket.models.pipeline_config import PipelineKnownHostUpdate
from bitbucket.models.pipeline_config import PipelineSshKeyPairUpdate
from bitbucket.models.pipeline_config import PipelinesConfigUpdate

from bitbucket_unofficial_cli.output.columns import BUILD_NUMBER
from bitbucket_unofficial_cli.output.columns import CACHES
from bitbucket_unofficial_cli.output.columns import CACHE_URI
from bitbucket_unofficial_cli.output.columns import KNOWN_HOSTS
from bitbucket_unofficial_cli.output.columns import PIPELINES_CONFIG
from bitbucket_unofficial_cli.output.columns import SSH_KEY_PAIR
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.secrets import read_secret
from bitbucket_unofficial_cli.services.secrets import read_secret_file

CONFIG_APP: Final = typer.Typer(help="Pipelines settings of a repository.", no_args_is_help=True)
KEY_APP: Final = typer.Typer(help="The SSH key pair pipelines use.", no_args_is_help=True)
HOST_APP: Final = typer.Typer(help="Known SSH hosts for pipelines.", no_args_is_help=True)
CACHE_APP: Final = typer.Typer(help="Pipeline caches.", no_args_is_help=True)

HostUuid = Annotated[str, typer.Argument(help="Known host UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
CacheUuid = Annotated[str, typer.Argument(help="Cache UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    repo: Repo
    enabled: Annotated[bool, typer.Option("--enabled/--disabled", help="Turn pipelines on or off.")]


@dataclass(frozen=True, slots=True, kw_only=True)
class _BuildNumberOptions:
    repo: Repo
    next_number: Annotated[int, typer.Option("--next", help="Number the next pipeline gets.")]


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetKeyOptions:
    repo: Repo
    private_key_file: Annotated[Path | None, typer.Option("--private-key-file", help="File with the private key.")] = (
        None
    )
    stdin: Annotated[bool, typer.Option("--stdin", help="Read the private key from stdin.")] = False
    public_key: Annotated[str | None, typer.Option("--public-key", help="The matching public key.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@dataclass(frozen=True, slots=True, kw_only=True)
class _HostOptions:
    repo: Repo
    hostname: Annotated[str | None, typer.Option("--hostname", help="Host name.")] = None
    key_type: Annotated[str | None, typer.Option("--key-type", help="Key type, e.g. ssh-ed25519.")] = None
    key: Annotated[str | None, typer.Option("--key", help="The host's public key.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateHostOptions(_HostOptions):
    uuid: HostUuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteHostOptions:
    repo: Repo
    uuid: HostUuid
    yes: Yes = False


def _public_key(options: _HostOptions) -> dict[str, str] | None:
    key = {"key_type": options.key_type, "key": options.key}
    present = {name: value for name, value in key.items() if value is not None}
    return present or None


@CONFIG_APP.command(name="get", help="Show whether pipelines are enabled.")
@handle_errors
def get_config(ctx: typer.Context, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).pipelines_config.get(), PIPELINES_CONFIG, id_key="enabled"))


@CONFIG_APP.command(name="update", help="Turn pipelines on or off.")
@handle_errors
@options_from(_UpdateOptions)
def update_config(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    config = app_context.repository(options.repo).pipelines_config
    updated = config.update(build(PipelinesConfigUpdate, enabled=options.enabled))
    app_context.render(single(updated, PIPELINES_CONFIG, id_key="enabled"))


@CONFIG_APP.command(name="build-number", help="Set the number the next pipeline gets.")
@handle_errors
@options_from(_BuildNumberOptions)
def build_number(ctx: typer.Context, options: _BuildNumberOptions) -> None:
    app_context = get_app_context(ctx)
    config = app_context.repository(options.repo).pipelines_config
    updated = config.update_build_number(build(PipelineBuildNumberUpdate, next=options.next_number))
    app_context.render(single(updated, BUILD_NUMBER, id_key="next"))


@KEY_APP.command(name="get", help="Show the public key of the pipelines key pair.")
@handle_errors
def get_key(ctx: typer.Context, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(
        single(app_context.repository(repo).pipelines_config.ssh_key_pair.get(), SSH_KEY_PAIR, id_key="public_key")
    )


@KEY_APP.command(name="set", help="Replace the key pair; the private key comes from a file or stdin.")
@handle_errors
@options_from(_SetKeyOptions)
def set_key(ctx: typer.Context, options: _SetKeyOptions) -> None:
    app_context = get_app_context(ctx)
    if options.private_key_file is not None:
        private_key = read_secret_file(options.private_key_file)
    else:
        private_key = read_secret("private key", from_stdin=options.stdin)
    payload = build(PipelineSshKeyPairUpdate, private_key=private_key, public_key=options.public_key)
    updated = app_context.repository(options.repo).pipelines_config.ssh_key_pair.update(payload)
    app_context.render(single(updated, SSH_KEY_PAIR, id_key="public_key"))


@KEY_APP.command(name="delete", help="Delete the key pair.")
@handle_errors
def delete_key(ctx: typer.Context, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm("Delete the pipelines SSH key pair?", assume_yes=yes)
    app_context.repository(repo).pipelines_config.ssh_key_pair.delete()
    app_context.notify("Deleted the pipelines SSH key pair.")


@HOST_APP.command(name="list", help="List the known hosts.")
@handle_errors
@options_from(_ListOptions)
def list_hosts(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    hosts = app_context.repository(options.repo).pipelines_config.known_hosts
    found = paged(app_context, options, hosts.list, hosts.list_page)
    app_context.render(many(found, KNOWN_HOSTS, id_key="uuid"))


@HOST_APP.command(name="get", help="Show a known host.")
@handle_errors
def get_host(ctx: typer.Context, uuid: HostUuid, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    host = app_context.repository(repo).pipelines_config.known_hosts.get(uuid)
    app_context.render(single(host, KNOWN_HOSTS, id_key="uuid"))


@HOST_APP.command(name="create", help="Add a known host.")
@handle_errors
@options_from(_HostOptions)
def create_host(ctx: typer.Context, options: _HostOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        PipelineKnownHostCreate, options.from_file, hostname=options.hostname, public_key=_public_key(options)
    )
    created = app_context.repository(options.repo).pipelines_config.known_hosts.create(payload)
    app_context.render(single(created, KNOWN_HOSTS, id_key="uuid"))


@HOST_APP.command(name="update", help="Change a known host.")
@handle_errors
@options_from(_UpdateHostOptions)
def update_host(ctx: typer.Context, options: _UpdateHostOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        PipelineKnownHostUpdate, options.from_file, hostname=options.hostname, public_key=_public_key(options)
    )
    updated = app_context.repository(options.repo).pipelines_config.known_hosts.update(options.uuid, payload)
    app_context.render(single(updated, KNOWN_HOSTS, id_key="uuid"))


@HOST_APP.command(name="delete", help="Delete a known host.")
@handle_errors
@options_from(_DeleteHostOptions)
def delete_host(ctx: typer.Context, options: _DeleteHostOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete known host '{options.uuid}'?", assume_yes=options.yes)
    app_context.repository(options.repo).pipelines_config.known_hosts.delete(options.uuid)
    app_context.notify(f"Deleted known host '{options.uuid}'.")


@CACHE_APP.command(name="list", help="List the caches of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_caches(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    caches = app_context.repository(options.repo).pipelines_config.caches
    found = paged(app_context, options, caches.list, caches.list_page)
    app_context.render(many(found, CACHES, id_key="uuid"))


@CACHE_APP.command(name="uri", help="Show where a cache's content can be downloaded.")
@handle_errors
def cache_uri(ctx: typer.Context, uuid: CacheUuid, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    found = app_context.repository(repo).pipelines_config.caches.content_uri(uuid)
    app_context.render(single(found, CACHE_URI, id_key="uri"))


@CACHE_APP.command(name="delete", help="Delete a cache.")
@handle_errors
def delete_cache(ctx: typer.Context, uuid: CacheUuid, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete cache '{uuid}'?", assume_yes=yes)
    app_context.repository(repo).pipelines_config.caches.delete(uuid)
    app_context.notify(f"Deleted cache '{uuid}'.")


@CACHE_APP.command(name="delete-by-name", help="Delete every cache with a name.")
@handle_errors
def delete_caches_by_name(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Cache name.")],
    repo: Repo,
    *,
    yes: Yes = False,
) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete every cache named '{name}'?", assume_yes=yes)
    app_context.repository(repo).pipelines_config.caches.delete_by_name(name)
    app_context.notify(f"Deleted the caches named '{name}'.")
