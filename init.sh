#!/bin/bash
cat dump_kong.sql | docker exec -i kong-konga-keycloak_kong-db_1 psql -U kong -d postgres
cat dump_keycloak.sql | docker exec -i kong-konga-keycloak_keycloak-db_1 psql -U keycloak -d postgres
