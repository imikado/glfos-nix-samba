# GLF OS nix samba

# to launch Project

## on linux with nix

```bash
nix develop
python src/main.py
```


# localization

```bash
xgettext -d base -o src/infrastructure/locales/nix-samba.pot src/main.py


```

## on linux with docker

only once

```bash
./buildDocker.sh
````

then

```bash
./runWithDocker.sh
````
