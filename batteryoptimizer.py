import asyncio
from datetime import datetime

from appdaemon import adbase as ad      # Minimalist app base
from appdaemon.entity import Entity
from appdaemon.adapi import ADAPI       # Basic API
from appdaemon.plugins.hass import Hass # Home Assistant-specific API


class BatteryOptimizer(Hass):
    overallOnOff = "input_boolean.enablebatteryoptimizer"
    gridStatus = "binary_sensor.enpower_202446023084_grid_status"
    batteryTotal = "sensor.envoy_122042083566_battery"
    production = "sensor.envoy_122042083566_current_power_production"

    downstairsACEntity = "climate.downstairs"
    upstairsACEntity = "climate.upstairs"
    #originally climate.set_temperature
    serviceCallToSetTemperature = "set_temperature"
    #originally button.press
    serviceCallToPressButton = "press"
    downstairsClearHold = "button.downstairs_clear_hold"
    upstairsClearHold = "button.upstairs_clear_hold"

    # acEntityMode = "hvac_mode"
    acTargetTemperature = "temperature"

    hasOptimizedOnce = False
    # ha: Hass
    adapi: ADAPI
    def initialize(self):
        self.adapi = self.get_ad_api()
        result = self.adapi.run_every(self.run_every_cycle, "now", 900)
        result2 = self.adapi.run_once(self.run_every_cycle, "now")
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
        if (batteryPercent is None or panelProduction is None) or (isinstance(batteryPercent, dict) or isinstance(panelProduction, dict)):
            self.adapi.log("Error getting battery percent or panel production, skipping optimization...")
            return
        batteryPercent = float(batteryPercent)
        panelProduction = float(panelProduction)
        # self.adapi.log(f"BatteryPercent: {type(batteryPercent)}, PanelProduction: {type(panelProduction)}")
        # self.adapi.log(f"BatteryPercent: {batteryPercent}, PanelProduction: {panelProduction}")
        # for key, value in batteryPercent.items():
        #     self.adapi.log(f"BatteryPercent key: {key}, value: {value}")
        entityDownstairsAc = self.adapi.get_entity(self.downstairsACEntity)
        entityUpstairsAc = self.adapi.get_entity(self.upstairsACEntity)
        entityDownstairsClearHold = self.adapi.get_entity(self.downstairsClearHold)
        entityUpstairsClearHold = self.adapi.get_entity(self.upstairsClearHold)
        self.adapi.log(f"Battery at {batteryPercent} %, production at {panelProduction} kW, optimizing...")

        self.OptimizeAC(batteryPercent, panelProduction, entityDownstairsAc, entityDownstairsClearHold)
        self.OptimizeAC(batteryPercent, panelProduction, entityUpstairsAc, entityUpstairsClearHold)
        self.adapi.log(f"Completed battery optimization routine...")

    def OptimizeAC(self, batteryPercent, panelProduction, acEntity : Entity, clearHoldEntity : Entity):
        try:
            if acEntity.state == "cool":
                if batteryPercent > 90 and panelProduction > 1.0:
                    self.adapi.log(f"Battery at {batteryPercent}%, production at {panelProduction}kW, overcooling {acEntity.entity_name} AC...")
                    acEntity.call_service(self.serviceCallToSetTemperature, temperature = 68)
                    # 20260519 - these were all failed attempts at interacting with the evil 4.5.14 dev tagged container...
                    # acEntity.call_service(self.serviceCallToSetTemperature, timeout=-1, temperature=68)
                    # syncResult = self.adapi.call_service(f"{acEntity.domain}/{self.serviceCallToSetTemperature}", acEntity.namespace, entity_id=acEntity.entity_id, temperature=68)
                    # needAwait = self._entity_service_call(self.serviceCallToSetTemperature, acEntity.entity_id, namespace=acEntity.namespace, temperature=68)
                    # needAwait = self.call_service(f"{acEntity.domain}/{self.serviceCallToSetTemperature}", acEntity.namespace, temperature=68)
                    # resultOfAwait = asyncio.run(needAwait)
                    self.hasOptimizedOnce = True
                else:
                    self.adapi.log(f"Battery at {batteryPercent}%, production at {panelProduction}kW, clearing hold...")
                    self.ClearHold(clearHoldEntity)
        except Exception as e:
            self.adapi.log(f"Error optimizing AC {acEntity.name}: {e}")
    def ClearHold(self, clearHoldEntity : Entity):
        try:
            self.adapi.log(f"Clearing hold for {clearHoldEntity.name}...")
            clearHoldEntity.call_service(self.serviceCallToPressButton)
        except Exception as e:
            self.adapi.log(f"Error clearing hold for {clearHoldEntity.name}: {e}")

def main():
    print("Hello from battery-optimizer!")

if __name__ == "__main__":
    main()
