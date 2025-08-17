import type { IncomingToBackground, OutgoingFromBackground } from './types';

export function sendMessageToBackground(message: IncomingToBackground): Promise<OutgoingFromBackground> {
  return new Promise((resolve, reject) => {
    try {
      if (!chrome?.runtime?.sendMessage) return reject(new Error('Messaging not available'));
      chrome.runtime.sendMessage(message, (resp: OutgoingFromBackground) => {
        if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
        resolve(resp);
      });
    } catch (e) {
      reject(e);
    }
  });
}



