import { RegisteredModuleType } from "./Module";

export type CommandSchema ={
    servo: {
        setAngle: {
            angle: number;
            isPivot: boolean;
        },
        setPivotAngle:{
            pivotAngle: number;
        },
        setPivotLimits:{
            pivotMin: number;
            pivotMax: number;
        },
        setIsPivot:{
            isPivot: boolean;
        }

    },
    led: {
        toggle:{},
        setState: {
            state: boolean;
        },
        setBrightness: {
           brightness: number;
        }
    } ,
    buzzer: {
        on: {},
        off: {},
        setPulse: {
            count: number;
            duration: number;
        }
    }



}

export type ModuleType = keyof CommandSchema;

export type CommandName<TModuleType extends ModuleType> =
  keyof CommandSchema[TModuleType];


export type CommandPayload<
  TModuleType extends ModuleType,
  TCommandName extends CommandName<TModuleType>
> = CommandSchema[TModuleType][TCommandName];



export function sendCommand<
  TModuleType extends RegisteredModuleType,
  TCommandName extends CommandName<TModuleType>
>(
  moduleId: string,
  moduleType: TModuleType,
  commandName: TCommandName,
  payload: CommandPayload<TModuleType, TCommandName>
) {
  const packet = {
    cmd: commandName,
    id: moduleId,
    type: moduleType,
    payload,
  };

  window.api.sendCommand(packet);
}