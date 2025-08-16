// Chrome Extension API types
declare namespace chrome {
  namespace runtime {
    interface MessageSender {
      id?: string;
      url?: string;
      origin?: string;
      tab?: chrome.tabs.Tab;
    }
    
    function sendMessage(message: any): Promise<any>;
    function sendMessage(extensionId: string, message: any): Promise<any>;
    function sendMessage(message: any, responseCallback?: (response: any) => void): void;
    
    const onMessage: {
      addListener(callback: (message: any, sender: MessageSender, sendResponse: (response?: any) => void) => void): void;
    };
    
    const onInstalled: {
      addListener(callback: (details: { reason: string }) => void): void;
    };
  }
  
  namespace storage {
    interface StorageArea {
      get(keys?: string | string[] | { [key: string]: any } | null): Promise<{ [key: string]: any }>;
      set(items: { [key: string]: any }): Promise<void>;
      remove(keys: string | string[]): Promise<void>;
      clear(): Promise<void>;
    }
    
    const local: StorageArea;
    const sync: StorageArea;
  }
  
  namespace tabs {
    interface Tab {
      id?: number;
      url?: string;
      title?: string;
    }
    
    function query(queryInfo: { active?: boolean; currentWindow?: boolean }): Promise<Tab[]>;
    function sendMessage(tabId: number, message: any): Promise<any>;
    function sendMessage(tabId: number, message: any, responseCallback?: (response: any) => void): void;
  }
}
