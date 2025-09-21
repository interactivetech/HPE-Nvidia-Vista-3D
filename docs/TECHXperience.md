## ssh to lab server
ssh ssh.axisapps.io  -l 7ceb032279654a1881e3964dc32028b6

# port forward lab server port 8001 so the localhost can see it
ssh ssh.axisapps.io  -l 7ceb032279654a1881e3964dc32028b6 -L 8001:localhost:8001

## port forward local image server so the lab server can see it
ssh -N -R 0.0.0.0:8888:localhost:8888 7ceb032279654a1881e3964dc32028b6@ssh.axisapps.io
