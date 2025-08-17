// Small UUIDv4 generator without external deps
export function v4(): string {
  // crypto available in MV3/vscode webview; fallback to Math.random if absent
  const cryptoObj: Crypto | undefined = (globalThis as any).crypto;
  if (cryptoObj?.getRandomValues) {
    const buf = new Uint8Array(16);
    cryptoObj.getRandomValues(buf);
    // per RFC 4122
    buf[6] = (buf[6] & 0x0f) | 0x40;
    buf[8] = (buf[8] & 0x3f) | 0x80;
    const b = Array.from(buf).map((x) => x.toString(16).padStart(2, '0'));
    return `${b[0]}${b[1]}${b[2]}${b[3]}-${b[4]}${b[5]}-${b[6]}${b[7]}-${b[8]}${b[9]}-${b[10]}${b[11]}${b[12]}${b[13]}${b[14]}${b[15]}`;
  }
  // weak fallback
  const s4 = () => (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
  return `${s4()}${s4()}-${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`;
}

export { v4 as uuidv4 };


