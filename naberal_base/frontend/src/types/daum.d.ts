/**
 * Daum Postcode API type declarations.
 * Loaded via external script: https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js
 */

interface DaumPostcodeResult {
  zonecode: string;
  roadAddress: string;
  jibunAddress: string;
  userSelectedType: "R" | "J";
  buildingName: string;
  apartment: string;
  address: string;
}

interface DaumPostcodeOptions {
  oncomplete: (data: DaumPostcodeResult) => void;
  onclose?: () => void;
  width?: string | number;
  height?: string | number;
}

interface DaumPostcodeInstance {
  open: (params?: Record<string, unknown>) => void;
  embed: (container: HTMLElement) => void;
}

interface DaumPostcodeConstructor {
  new (options: DaumPostcodeOptions & Record<string, unknown>): DaumPostcodeInstance;
}

interface DaumNamespace {
  Postcode: DaumPostcodeConstructor;
}

interface Window {
  daum?: DaumNamespace;
}
