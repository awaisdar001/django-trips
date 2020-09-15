# DestinationPakistan MFE(MicoFrontEnd)

microfrontend for DestinationPak.com


## Project Setup
1. In order to use the app, make sure you have installed docker and docker compose.
2. Clone the repo 
```bash
git clone {git-clone-repo-url}
```
3. Change the directory to the project folder. 
```bash
cd {project-dir}/djreact
```
4. Build the docker image. 
```bash
make build
```
5. Run the docker container
```bash
make run
```

6. Once that is done, you should be able to ssh/log/attach the docker container. 
6.1 Get logs
```bash
make logs
```
6.2 Attach container
```bash
make app-attach
```

6.3 Restart container
```bash
make app-restart
```

6.4 Open container bash
```bash
make app-shell
```
6.4 Stop container
```bash
make stop
```

6.5 Destory container. Use with care, this will remove all devstack-related containers, networks, and volumes
```bash
make destroy
```

## Run Project
1. The `make` file contains most of the commands to be run the container. 
`make run`
Once the app has been run, it should be available at `http://localhost:9990/api/trips/`

2. Run the frontend by following.
```bash
make app-shell
cd mfe
npm run
```
The MFE is available at `http://localhost:3002/`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
