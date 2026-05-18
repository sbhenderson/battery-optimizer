# Battery Optimizer

This is a VERY simple [AppDaemon](https://www.appdaemon.org/) application for the purposes of working with the Enphase Envoy, Ecobee thermostats, and a Wallbox charger. It will **not** be generic, but it may offer ideas.

## Theory of the control

TBD

## Setup

On the server running Home Assistant, I added another service:

```yml
  appdaemon:
    image: acockburn/appdaemon:dev
    container_name: appdaemon
    secrets:
      - app_daemon_ha_token
    environment:
      - HA_URL=https://homeassistant.henderson.engineering/
      - TOKEN=eyJh...
      - DASH_URL=http://appdaemon:5050
    volumes:
      - /opt/ryzenserver/appdaemon:/conf
    # command: -D DEBUG
    restart: unless-stopped
    networks:
      userNetwork1:
```

I would use the Docker secret for the token, but it doesn't seem happy.

After that, I run it behind Traefik. I was really struggling with that dash_url because the websocket kept dieing all the time. After testing it directly (direct to an IP address), I determined that the aui (Admin user interface) is borked probably for some easy reason.

Therefore, todo items for appdaemon when I have a tiny amount more time:

1. Check if token starts with a / and if so, read the secret from the file.
2. Attempt to look at the websocket issue.