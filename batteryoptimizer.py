from datetime import datetime

from appdaemon import adbase as ad      # Minimalist app base
from appdaemon.entity import Entity
from appdaemon.adapi import ADAPI       # Basic API
from appdaemon.plugins.hass import Hass # Home Assistant-specific API


class BatteryOptimizer(ad.ADBase):
    overallOnOff = "input_boolean.enablebatteryoptimizer"
    gridStatus = "binary_sensor.enpower_202446023084_grid_status"
    batteryTotal = "sensor.envoy_122042083566_battery"
    production = "sensor.envoy_122042083566_current_power_production"

    downstairsACEntity = "climate.downstairs"
    upstairsACEntity = "climate.upstairs"
    downstairsClearHold = "button.downstairs_clear_hold"
    upstairsClearHold = "button.upstairs_clear_hold"

    # acEntityMode = "hvac_mode"
    acTargetTemperature = "temperature"

    hasOptimizedOnce = False
    adapi: ADAPI
    # ha: Hass
    def initialize(self):
        self.adapi = self.get_ad_api()
        # self.ha = self.get_plugin_api("HASS")
        result = self.adapi.run_every(self.run_every_cycle, "now", 900)
        self.adapi.log("Battery Optimizer initialized!")
        
    def run_every_cycle(self, **kwargs):
        time = datetime.now()
        self.adapi.log(f"Running battery optimization routine at {time}...")
        overallDisabled = self.adapi.get_state(self.overallOnOff) == "on"
        if not overallDisabled:
            self.adapi.log("Battery optimization routine is disabled, skipping...")
            return
        gridOnline = self.adapi.get_state(self.gridStatus) == "on"
        entityDownstairsClearHold = self.adapi.get_entity(self.downstairsClearHold)
        entityUpstairsClearHold = self.adapi.get_entity(self.upstairsClearHold)
        if not gridOnline:
            if self.hasOptimizedOnce:
                self.adapi.log("Grid is offline, clearing holds and skipping battery optimization routine...")
                self.ClearHold(entityDownstairsClearHold)
                self.ClearHold(entityUpstairsClearHold)
                self.hasOptimizedOnce = False
            else:
                self.adapi.log("Grid is offline, skipping battery optimization routine...")
            return
        current_hour = time.hour
        if current_hour < 5 or current_hour >= 21:
            # don't have to worry about resetting here because the ecobee will clear hold as part of changing mode
            self.adapi.log("Outside of optimization hours, skipping...")
            self.hasOptimizedOnce = False
            return
        batteryPercent = self.adapi.get_state(self.batteryTotal)
        panelProduction = self.adapi.get_state(self.production)
        entityDownstairsAc = self.adapi.get_entity(self.downstairsACEntity)
        entityUpstairsAc = self.adapi.get_entity(self.upstairsACEntity)
        entityDownstairsClearHold = self.adapi.get_entity(self.downstairsClearHold)
        entityUpstairsClearHold = self.adapi.get_entity(self.upstairsClearHold)

        self.OptimizeAC(batteryPercent, panelProduction, entityDownstairsAc, entityDownstairsClearHold)
        self.OptimizeAC(batteryPercent, panelProduction, entityUpstairsAc, entityUpstairsClearHold)
        self.hasOptimizedOnce = True


    def OptimizeAC(self, batteryPercent, panelProduction, acEntity : Entity, clearHoldEntity : Entity):
        try:
            if acEntity.state == "cool":
                if batteryPercent > 85 and panelProduction > 1.0:
                    self.adapi.log(f"Battery at {batteryPercent}%, production at {panelProduction}kW, overcooling {acEntity.name} AC...")
                    acEntity.call_service("climate.set_temperature", data={"temperature": 68})
                else:
                    self.adapi.log(f"Battery at {batteryPercent}%, production at {panelProduction}kW, clearing hold...")
                    self.ClearHold(clearHoldEntity)
        except Exception as e:
            self.adapi.log(f"Error optimizing AC {acEntity.name}: {e}")
    def ClearHold(self, clearHoldEntity : Entity):
        try:
            self.adapi.log(f"Clearing hold for {clearHoldEntity.name}...")
            clearHoldEntity.call_service("button.press")
        except Exception as e:
            self.adapi.log(f"Error clearing hold for {clearHoldEntity.name}: {e}")

def main():
    print("Hello from battery-optimizer!")

if __name__ == "__main__":
    main()
