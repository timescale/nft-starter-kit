## TimescaleDB + Superset dashboard setup

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker compose](https://docs.docker.com/compose/install/)

    Verify that both are installed:
    ```bash
    docker --version && docker-compose --version
    ```

### Instructions

1. Clone the repo:
    ```bash
    git clone https://github.com/timescale/wip-crypto-starter
    ```
1. Run `docker-compose up --build` in the /docker folder:
    ```bash
    cd  wip-crypto-starter/docker
    docker-compose up --build
    ```
    See when the process is done (it could take a couple of minutes):
    ```bash
    timescaledb_1      | PostgreSQL init process complete; ready for start up.
    ```
1. Go to http://0.0.0.0:8088/ in your browser and login with these credentials:
    ```txt
    user: admin
    password: admin
    ```
1. Open the `Databases` page inside Superset (http://0.0.0.0:8088/databaseview/list/). You will see exactly one item there
    called `Crypto V2`.
1. Click the edit button (pencil icon) on the right side of the table (under "Actions").
1. Don't change anything in the popup window, just click `Finish`. This will make sure the database can be 
    reached from Superset.
1. Go check out your NFT dashboards! 

    Collections dashboard: http://0.0.0.0:8088/superset/dashboard/1

    Assets dashboard: http://0.0.0.0:8088/superset/dashboard/2 

    You can also play with the filters!
