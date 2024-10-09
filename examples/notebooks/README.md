# Docker notebook

Use local notebook and output directories (`./app`) with the container's jupyter kernel.

```bash
docker pull hub.kerga.fr/flexpipe:latest

docker run --rm -p 8888:8888 --name flex_nb_ct -v ./app:/work hub.kerga.fr/flexpipe:latest

docker run -it --rm -v ./app:/work flex_nb bash  # debug
```

Open URL: `http://127.0.0.1:8888/lab?token=XXX`.

## In VSCode

You need to select the jupyter kernel to match the server IP/token:

`http://127.0.0.1:8888/lab?token=XXX`
