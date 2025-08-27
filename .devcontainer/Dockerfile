# Usa l'immagine base di Python
FROM python:3.13.0-bookworm

# Setta la directory di lavoro
WORKDIR /workspaces/flume-ledger

ENV PYTHONPATH=/workspaces/flume-ledger/app


# Installa le dipendenze di sistema richieste e Rust
RUN apt-get update && \
    apt-get install -y \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgl1 \
        libglx-mesa0 \
        libglib2.0-0 \
        libgtk2.0-dev \
        curl \
        sudo

# Create a non-root user 'vscode' and add it to the sudo group
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME --shell /bin/bash && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# Switch to non-root user
USER $USERNAME

# Install Rust as the vscode user
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable -c rustfmt --profile default --no-modify-path

# Add Rust to the PATH for the vscode user
ENV PATH="/home/$USERNAME/.cargo/bin:${PATH}"
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

ENV ENV_PATH envs/.env

# Comando di avvio
CMD ["uvicorn", "app.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]

