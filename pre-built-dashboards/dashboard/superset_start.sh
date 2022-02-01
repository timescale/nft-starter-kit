#!/bin/bash 
superset fab create-admin \
            --username admin \
            --firstname Superset \
            --lastname Admin \
            --email admin@email.com \
            --password admin      
superset db upgrade
superset init
superset import_datasources -p sources.yaml
superset set_database_uri -d "NFT Starter Kit" -u postgresql://docker:password@timescaledb:5432/starter_kit
superset import_dashboards -p dash.json
echo '****************Superset is starting up****************'
echo '****************Go to http://0.0.0.0:8088/ to login****************'
superset run -p 8088 --host 0.0.0.0