export interface SiteAdapter {
  id: string;
  matches(loc: Location): boolean;
  findInput(doc?: Document): HTMLTextAreaElement | HTMLElement | null;
  findSendButton(doc?: Document): HTMLButtonElement | null;
  getDraft(el: HTMLElement | HTMLTextAreaElement): string;
  setDraft(el: HTMLElement | HTMLTextAreaElement, text: string): void;
  anchorForButton(sendBtn: HTMLButtonElement): HTMLElement; // where to place our button
}


