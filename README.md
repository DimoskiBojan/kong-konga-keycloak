# kong-konga-keycloak
Note: when using docker build and docker-compose make sure you are in the right directory.

See information about functionalities and things of interest at [https://docs.google.com/document/d/1ENcb4lMzz0dn91iQT1mzSpG1OSQUXCDHwbYVyXDEFX4/edit](https://docs.google.com/document/d/1ENcb4lMzz0dn91iQT1mzSpG1OSQUXCDHwbYVyXDEFX4/edit). For now start by logging in at [http://localhost:8000/users/login](http://localhost:8000/users/login).

## SHORT SETUP

On the first start:

Initialize the configuration for Kong and Keycloak:
```bash
./init.sh
```
Patch/set the kong-oidc discovery and introspection endpoints with the current PC’s local IP address
(make sure the kong container is up and running):
```bash
python patch-kong-oidc.py
```

The next time we want to start the containers, we can just use 'docker-compose up -d'.


## NOT-DOCKERIZED

### USERS SERVICE (port 3000)
Commented in docker-compose.yml because of issue with LOCAL_IP inside of container.

Implementing user management with Keycloak, decoding token.

Run this service with the following command (make sure you are in the right directory), for now:
```bash
uvicorn users:app --reload --port 3000
```


## STEPS FOR FULL SETUP

### KONG (port 8000)

First, we need to create a Kong image with the kong-oidc plugin installed. 
```bash
docker build -t kong:2.0.0-alpine-oidc .
```
Next, we start the kong-db service (the database server Kong will use):
```bash
docker-compose up –d kong-db
```
Then we launch the kong migrations (we run the kong migrations only once on first setup):
```bash
docker-compose run --rm kong kong migrations bootstrap
```
And finally we can start kong(with the oidc plugin installed):
```bash
docker-compose up -d kong
```

### KONGA (port 1337)

Next, we start Konga:
```bash
docker-compose up -d konga
```

### KEYCLOAK (port 8180)

We start the keycloak database service:
```bash
docker-compose up -d keycloak-db
```
We start the keycloak service:
```bash
docker-compose up -d keycloak
```

### FASTAPI APP (port 5000)

We build the fastapi image with our app:
```bash
docker build -t uvicorn-fastapi-sqlalchemy .
```
We start the fastapi service:
```bash
docker-compose up -d fastapi
```
### VERIFY SERVICES

We check that everything is running with:
```bash
docker-compose ps
```

### INITIALIZE KONG & KEYCLOAK CONFIGS

Run the bash script init.sh, which will copy the configs for Kong and Keycloak to the volumes of their containers:

```bash
./init.sh
```

#### Change local IP address in kong-oidc config if you change network, or first init

Run the python script patch-kong-oidc.py. (Make sure the containers are up!)