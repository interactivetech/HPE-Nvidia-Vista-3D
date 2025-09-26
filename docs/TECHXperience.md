
#!/bin/bash
# Script to set up multiple reverse port forwards

# Replace these variables with your own values
USER="d47ef8093d8843c6a5a0df68b1508b2c"
SSH_SERVER="ssh.axisapps.io"

# The SSH command with multiple -R flags
ssh -N \
  -L 0.0.0.0:8000:localhost:8000 \
  -L 0.0.0.0:8501:localhost:8501 \
  -R 0.0.0.0:8888:localhost:8888 \
  ${USER}@${SSH_SERVER}

echo "Reverse port forwarding session started. Press Ctrl+C to terminate."
