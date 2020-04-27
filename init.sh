#!/bin/bash
docker cp ./volumes/kong kong-konga-keycloak_kong-db_:/var/lib/postgresql/data
docker cp ./volumes/keycloak kong-konga-keycloak_keycloak-db_1:/var/lib/postgresql/data
