# bin

A bunch of random scripts I keep on my `PATH`.

## Install

To install, just run

```sh
make install
```

The install procedure will

- Check if [github.com/adelynnmckay/bin](https://github.com/adelynnmckay/bin) is cloned to `~/.local/share/ade/bin`, and clone it if not.
- Symlink all files in `~/.local/share/ade/bin/src` that match `*.sh` or `*.py` to `~/.bin` with their extension stripped.
- If a file already exists in `~/.bin` with the same name, and it's not a symlink to a script in `~/.local/share/ade/bin/src`, then it is backed up in `~/.bin` with a `.bak` extension.
- If a `.bak` file already exist, the script throws an error.