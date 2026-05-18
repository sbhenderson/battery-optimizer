from appdaemon import adbase as ad      # Minimalist app base
from appdaemon.adapi import ADAPI       # Basic API
from appdaemon.plugins.hass import Hass # Home Assistant-specific API


class BatteryOptimizer(ad.ADBase):
    overallOnOff = "input_boolean.enablebatteryoptimizer"
    gridStatus = "binary_sensor.enpower_202446023084_grid_status"
    batteryTotal = "sensor.envoy_122042083566_battery"
    production = "sensor.envoy_122042083566_current_power_production"

    downstairsACEntity = "climate.downstairs"
    upstairsACEntity = "climate.upstairs"

    # acEntityMode = "hvac_mode"
    acTargetTemperature = "temperature"

    adapi: ADAPI
    # ha: Hass
    def initialize(self):
        self.adapi = self.get_ad_api()
        # self.ha = self.get_plugin_api("HASS")
        result = self.adapi.run_every(self.run_every_cycle, "now", 30)
        self.adapi.log("Battery Optimizer initialized!")
        
    def run_every_cycle(self, **kwargs):
        overallDisabled = self.adapi.get_state(self.overallOnOff) == "on"
        if not overallDisabled:
            self.adapi.log("Battery optimization routine is disabled, skipping...")
            return
        gridOnline = self.adapi.get_state(self.gridStatus) == "on"
        if not gridOnline:
            self.adapi.log("Grid is offline, skipping battery optimization routine...")
            return
        
        batteryPercent = self.adapi.get_state(self.batteryTotal)
        self.adapi.log(f"Running battery optimization routine BP: {batteryPercent}...")

        # if batteryPercent < 80 :


        # entityDownstairsAc = self.adapi.get_entity(self.downstairsACEntity)
        # entityUpstairsAc = self.adapi.get_entity(self.upstairsACEntity)
        # if entityDownstairsAc.state == "cool":

        # downstairsEntity = self.adapi.get_entity(self.downstairsACEntity)
        # downstairsEntityAttributes = downstairsEntity.attributes
        # self.adapi.log(f"Downstairs AC: {batteryPercent}...")
        # for x in downstairsEntityAttributes:
        #     self.adapi.log(f"{x} = {downstairsEntityAttributes[x]}")
        # downstairsState = downstairsEntity.state
        # self.adapi.log(f"Downstairs AC state: {downstairsState}...")
        


def main():
    print("Hello from battery-optimizer!")

if __name__ == "__main__":
    main()
