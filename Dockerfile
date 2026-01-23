FROM fedora:41

# Install dependencies
RUN dnf install -y \
    python3-devel \
    python3-gobject \
    gtk4-devel \
    libadwaita-devel \
    dbus-x11 \
    dconf \
    mesa-dri-drivers \
    && dnf clean all

RUN dnf install -y \
    libGLES \
    mesa-libGL \
    mesa-libEGL \
    vulkan-loader \
    mesa-vulkan-drivers

WORKDIR /app

# Fix for the dconf /run/user/1000 error
# We create a fake home-based dconf path if the system one is locked
ENV GIO_EXTRA_MODULES=/usr/lib64/gio/modules
ENV ADW_DEBUG_COLOR_SCHEME=prefer-dark

CMD ["python3", "src/main.py"]