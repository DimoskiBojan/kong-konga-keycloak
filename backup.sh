#!/bin/bash
mkdir ./volumes/kong
mkdir ./volumes/keycloak
docker cp kong-konga-keycloak_kong-db_1:/var/lib/postgresql/data ./volumes/kong
docker cp kong-konga-keycloak_keycloak-db_1:/var/lib/postgresql/data ./volumes/keycloak
