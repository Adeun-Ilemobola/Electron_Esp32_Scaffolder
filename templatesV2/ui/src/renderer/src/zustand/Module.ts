export type ServoPayload = {
  angle: number;
  pivotAngle: number;
  isPivot: boolean;
  pivotMin: number;
  pivotMax: number;

  config: {
    channel: number;
    angleMin: number;
    angleMax: number;
    pulseMin: number;
    pulseMax: number;
  };
};


export type LedPayload = {
  isOn: boolean;
  brightness: number;
};
export type BuzzerPayload = {
  state: boolean;
  pulseCount: number;
  pulseDuration: number;
};

export type ModulePayloadSchema = {
  servo: ServoPayload;
  led: LedPayload;
  buzzer: BuzzerPayload;
};

export type RegisteredModuleType = keyof ModulePayloadSchema;

