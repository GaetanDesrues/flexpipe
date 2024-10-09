# Docker notebook

```bash
docker build -t flex_nb . --no-cache
docker run -it --rm -v ./app:/work flex_nb bash  # debug
docker run --rm -p 8888:8888 --name flex_nb_ct -v ./app:/work flex_nb:latest
docker logs flex_nb_ct

docker run -d --name flex_nb_ct flex_nb:latest
docker stop flex_nb_ct
docker rm flex_nb_ct
docker rmi flex_nb

docker tag flex_nb:latest hub.kerga.fr/flexpipe:latest
docker push hub.kerga.fr/flexpipe:latest
```
