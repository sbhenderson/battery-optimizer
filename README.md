# Battery Optimizer

This is a VERY simple [AppDaemon](https://www.appdaemon.org/) application for the purposes of working with the Enphase Envoy, Ecobee thermostats, and a Wallbox charger. It will **not** be generic, but it may offer ideas.

[Blog post](https://scott.henderson.engineering/2026/05/18/home-power-2.html) can be found here.

## Theory of the control

This is all to maximize my consumption of electricity during daytime hours

This is some kind of Python pseudo code:

```py3
if not batteryOptimizerEnabled:
  #don't do stuff if human says no
  return
if not gridIsConnected:
  #should not do anything if I can't depend on the grid at night, but you never know?
  return
if hour < 5 or hour > 21:
  # undo any stateful actions during free use period
  enableCarCharger()
  return
if not acModeIsCooling:
  #don't need to do anything if the A/C isn't cooling
  return
if batteryPercent > 85 and productionInkW > 1.0:
  #cool this house
  setACsToOvercool()
  enableCarCharger()
else:
  clearHolds()
  disableCarCharger()
```

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

After that, I run it behind Traefik. I was really struggling with that dash_url because the websocket kept dying all the time. After testing it directly (direct to an IP address), I determined that the aui (Admin user interface) seems borked. Considering it must have worked, I bet it's a trivial issue that just requires running it locally.

Therefore, todo items for appdaemon when I have a tiny amount more time:

1. Check if token starts with a / and if so, read the secret from the file.
2. Attempt to look at the websocket issue.
