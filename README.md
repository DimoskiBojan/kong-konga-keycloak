# kong-konga-keycloak
Note: when using docker build and docker-compose make sure you are in the right directory.

Full explanation of functionalities and API Docs will be provided in the future. For now start by loggin in at [http://localhost:8000/login](http://localhost:8000/login).

## SHORT SETUP

We can start all our services using docker-compose:
```bash
docker-compose up -d
```
Then we need to initialize the configuration for Kong and Keycloak:
```bash
./init.sh
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

## NOT-DOCKERIZED
In the folder not-dockerized you will find fastapi services which are not yet dockerized, such as the users service.

### USERS SERVICE (port 3000)
Implementing user management with Keycloak, decoding token.

Run this service with the following command (make sure you are in the right directory), for now:
```bash
uvicorn users:app --reload --port 3000
```
