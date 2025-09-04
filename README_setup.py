# install docker
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# add user to docker
sudo usermod -aG docker ${USER}
newgrp docker

# install NVIDIA docker toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
sudo docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi

# install NGC CLI
wget --content-disposition https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.44.0/files/ngccli_linux.zip -O ngccli_linux.zip
unzip ngccli_linux.zip
cd ngc-cli
./install
ngc config set
ngc registry info

# add NGC CLI to BASH path
export PATH="$PATH:/home/${USER}/ngc-cli"

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install GitHub
sudo apt update
sudo apt install git
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# set up auth for github
gh auth login

# clone repository
gh repo clone dw-flyingw/Nvidia-Vista3d-segmenation

# set up venv
cd Nvidia-Vista3d-segmenation
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
uv sync

# Get the NVIDIA NIM
export NGC_API_KEY=<your personal NGC key>
export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p $LOCAL_NIM_CACHE

# create .env and change PROJECT_ROOT  and DICOM_FOLDER
cp dot_env_template .env

# place dicoms in dicom folder where each folder is a patient series

# start the Vista3d Docker
python utils/start_vista3d.py

# watch logs as it takes a while to start up 
docker logs vista3d -f

# create NiFTi files from Dicoms
python utils/dicom2nifti.py

# start https image server
python utils/image_server.py

# do segmentation
python utils/segment.py

# start gui
streamlit run app.py


