# Contributing

When contributing to this repository, please first discuss the change you wish
to make via issue, email, or any other method with the owners of this repository
before making a change.

Please note we have a code of conduct, please follow it in all your interactions
with the project.

## Issues and feature requests

You've found a bug in the source code, a mistake in the documentation or maybe
you'd like a new feature? You can help us by submitting an issue to our
[GitHub Repository][github]. Before you create an issue, make sure you search
the archive, maybe your question was already answered.

Even better: You could submit a pull request with a fix / new feature!

## Pull request process

1. Search our repository for open or closed [pull requests][prs] that relates
   to your submission. You don't want to duplicate effort.

1. You may merge the pull request in once you have the sign-off of two other
   developers, or if you do not have permission to do that, you may request
   the second reviewer to merge it for you.

## Development

### Start the app in the devcontainer

1. Open the repository in VS Code and choose **Reopen in Container**. The
   devcontainer runs a full Home Assistant with the supervisor.
1. Run the task **Start Home Assistant** (Terminal → Run Task). The first start
   takes a few minutes.
1. Open <http://localhost:7123> and finish the onboarding.
1. Go to **Settings → Apps → App store**. The app is listed under
   **Local apps**. Install and start it.
1. After changing files, click **Rebuild** on the app page so the changes are
   built into a new image.

Set the `verbose_level` option to `DEBUG` to see the full server log in the
**Log** tab.

### Debug the server without Home Assistant

This is the fastest way to test changes of the Python code. It builds the
image and starts the server directly, without the Home Assistant startup
scripts:

```bash
cd cybroscgiserver
docker build -t cybroscgiserver-dev .
docker run --rm -it --network host --entrypoint sh cybroscgiserver-dev -c '
  cd /usr/local/bin/scgi_server &&
  crudini --set config.ini ETH port 8442 &&
  crudini --set config.ini DEBUGLOG enabled true &&
  crudini --set config.ini DEBUGLOG verbose_level DEBUG &&
  crudini --set config.ini DEBUGLOG log_to_file false &&
  exec python3 scgi_server/start.py'
```

In a second terminal, check that the server answers:

```bash
curl "http://localhost:4000/?sys.server_version"
```

To test with your own configuration, mount it over the default one with
`-v /path/to/config.ini:/usr/local/bin/scgi_server/config.ini`.

### Run the linters

CI runs these checks on every pull request. To run them locally:

```bash
# shell scripts
shellcheck -s bash \
  cybroscgiserver/rootfs/etc/cont-init.d/*.sh \
  cybroscgiserver/rootfs/etc/services.d/cybroscgiserver/{run,finish}

# yaml
docker run --rm -v "$PWD:/w" -w /w cytopia/yamllint -c .yamllint .

# formatting
docker run --rm -v "$PWD:/w" -w /w node:22-alpine \
  npx -y prettier --check "**/*.{json,js,md,yaml}"
```

The Cybrotech server in `cybroscgiserver/rootfs/usr/local/bin/scgi_server/` is
excluded from Prettier (see `.prettierignore`), because it is copied unchanged
from Cybrotech.

### Update the Cybrotech server

Copy the new version from CybroEdgeToolkit into
`cybroscgiserver/rootfs/usr/local/bin/scgi_server/`. Then check these files,
which contain changes of this repository:

- `requirements.txt`: Cybrotech pins older versions of Django, Pillow and
  django-debug-toolbar that don't build on the Python version of the base
  image. Keep the newer versions.
- `lib/startup/runner.py`: `exit_code` must be created with
  `running_loop.create_future()`.
- Update the version in `README.md`, `cybroscgiserver/.README.j2` and
  `cybroscgiserver/DOCS.md`, and add an entry to `cybroscgiserver/CHANGELOG.md`.

Afterwards, start the server as described above to make sure it still runs.

[github]: https://github.com/killer0071234/hassio-cybroscgiserver/issues
[prs]: https://github.com/killer0071234/hassio-cybroscgiserver/pulls
