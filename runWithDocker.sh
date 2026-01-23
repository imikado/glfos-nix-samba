docker run -it \
    --rm \
    --net=host \
    -e DISPLAY=$DISPLAY \
    -e GSK_RENDERER=cairo \
    -e GDK_DEBUG=portals \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "$PWD:/app" \
    gtk4-python-dev