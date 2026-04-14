import platform
import shutil
import subprocess
import sys

import click
from core import setup

from modules.browser.session import get_session_info
from modules.browser.session_cdp import DEFAULT_CDP_PORT

# ── Chrome executable lookup ────────────────────────────────────────────

_CHROME_PATHS = {
    "Windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ],
    "Linux": [
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
    ],
}


def _find_chrome() -> str | None:
    """Return the Chrome executable path, or None if not found."""
    system = platform.system()
    candidates = _CHROME_PATHS.get(system, [])

    for path in candidates:
        if shutil.which(path) or __import__("os").path.isfile(path):
            return path
    return None


# ── CLI ─────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """Browser session utilities — extract auth tokens/cookies from Chrome."""
    pass


@cli.command("chrome-start")
@click.option(
    "-p",
    "--port",
    default=DEFAULT_CDP_PORT,
    show_default=True,
    help="Remote debugging port.",
)
@click.option(
    "--chrome-path",
    default=None,
    help="Explicit path to the Chrome executable. Auto-detected if omitted.",
)
@click.option(
    "--profile",
    "profile_dir",
    default=None,
    help="Chrome profile directory name (e.g. 'Default', 'Profile 1').",
)
def chrome_start(port: int, chrome_path: str | None, profile_dir: str | None):
    """Start Chrome with --remote-debugging-port for CDP access.

    This is required on Windows/Linux before using session extraction commands.
    On macOS this is optional (AppleScript is used by default).
    """
    chrome = chrome_path or _find_chrome()
    if not chrome:
        click.echo(
            "Error: Could not find Google Chrome.\nSpecify the path explicitly with --chrome-path.",
            err=True,
        )
        sys.exit(1)

    cmd = [chrome, f"--remote-debugging-port={port}"]
    if profile_dir:
        cmd.append(f"--profile-directory={profile_dir}")

    click.echo(f"Starting Chrome with remote debugging on port {port} ...")
    click.echo(f"  Executable : {chrome}")
    if profile_dir:
        click.echo(f"  Profile    : {profile_dir}")
    click.echo(f"  Command    : {' '.join(cmd)}")
    click.echo()
    click.echo("Chrome is running. Close this terminal or Ctrl+C to stop.")

    try:
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        click.echo("\nStopping Chrome ...")
        process.terminate()
    except FileNotFoundError:
        click.echo(f"Error: Chrome not found at '{chrome}'.", err=True)
        sys.exit(1)


@cli.command("session")
@click.argument("domain")
@click.option(
    "-ls",
    "--local-storage",
    multiple=True,
    help="localStorage key(s) to retrieve. Repeatable.",
)
@click.option(
    "-ck",
    "--cookie",
    multiple=True,
    help="Cookie name(s) to retrieve (exact match). Repeatable.",
)
@click.option(
    "-cp",
    "--cookie-prefix",
    multiple=True,
    help="Cookie name prefix(es) to retrieve. Repeatable.",
)
@click.option(
    "--backend",
    type=click.Choice(["auto", "applescript", "cdp"]),
    default="auto",
    show_default=True,
    help="Session extraction backend.",
)
@click.option(
    "-p",
    "--port",
    default=DEFAULT_CDP_PORT,
    show_default=True,
    help="CDP port (only used with --backend=cdp).",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def session(domain, local_storage, cookie, cookie_prefix, backend, port, as_json):
    """Extract session info (localStorage / cookies) from a Chrome tab.

    DOMAIN is the domain substring to match against open Chrome tab URLs.

    \b
    Examples:
      browser-cli session example.com -ls authToken
      browser-cli session myapp.io -ck session_id -cp wordpress_logged_in
      browser-cli session example.com -ls token --backend cdp --port 9222
    """
    ls_fields = list(local_storage) or None
    ck_fields = list(cookie) or None
    ck_prefixes = list(cookie_prefix) or None

    if not ls_fields and not ck_fields and not ck_prefixes:
        click.echo(
            "Error: Provide at least one of --local-storage, --cookie, or --cookie-prefix.",
            err=True,
        )
        sys.exit(1)

    resolved_backend = None if backend == "auto" else backend

    try:
        info = get_session_info(
            target_domain=domain,
            local_storage_fields=ls_fields,
            cookie_fields=ck_fields,
            cookie_prefixes=ck_prefixes,
            backend=resolved_backend,
            cdp_port=port,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(info.model_dump_json(indent=2))
    else:
        click.echo(f"Base URL : {info.base_url}")
        click.echo(f"Tab URL  : {info.tab_url}")
        if info.local_storage:
            click.echo("Local Storage:")
            for k, v in info.local_storage.items():
                click.echo(f"  {k} = {v}")
        if info.cookies:
            click.echo("Cookies:")
            for k, v in info.cookies.items():
                click.echo(f"  {k} = {v}")


def main():
    """Entry point for the Browser CLI."""
    setup()
    cli()


if __name__ == "__main__":
    main()
