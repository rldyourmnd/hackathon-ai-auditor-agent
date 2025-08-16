# 🔍 AI Auditor - Полное логирование процесса работы

## 🎯 Где смотреть логи

### 1. **Content Script (основная логика)**
- Откройте ChatGPT или Claude
- Нажмите **F12** → вкладка **Console**
- В фильтре введите: `AI Auditor` 

### 2. **Background Script (service worker)**
- Откройте `chrome://extensions/`
- Найдите "AI Auditor" 
- Кликните **"background page"** → DevTools → Console

### 3. **Popup (настройки)**
- Правый клик на иконку расширения
- **"Inspect popup"** → Console

---

## 📋 Полная последовательность логов

### **🚀 Инициализация (при загрузке страницы)**
```
🚀 AI Auditor content script loaded
🔍 [14:32:15] AI Auditor: 🚀 Initializing AI Auditor {readyState: "loading", url: "https://chatgpt.com"}
🔍 [14:32:15] AI Auditor: ⏳ Waiting for DOMContentLoaded
🔍 [14:32:16] AI Auditor: ✅ DOM loaded, starting initialization
🔍 [14:32:16] AI Auditor: ⚙️ Loading settings from storage
🔍 [14:32:16] AI Auditor: ✅ Settings loaded successfully {blockOnHighRisk: false, offlineMode: true}
```

### **🌐 Определение сайта**
```
🔍 [14:32:16] AI Auditor: 🌐 Starting site detection {url: "https://chatgpt.com/c/123", hostname: "chatgpt.com"}
🔍 [14:32:16] AI Auditor: ChatGPT detection on chatgpt.com {detected: true}
🔍 [14:32:16] AI Auditor: ✅ Site detected: ChatGPT
```

### **🔧 Поиск элементов интерфейса**
```
🔍 [14:32:17] AI Auditor: Found input element with selector: #prompt-textarea {tagName: "TEXTAREA", id: "prompt-textarea", className: "..."}
🔍 [14:32:17] AI Auditor: Found send button with selector: [data-testid="send-button"] {tagName: "BUTTON", className: "...", textContent: "Send message"}
```

### **💉 Внедрение кнопки анализа**
```
🔍 [14:32:17] AI Auditor: Initializing for ChatGPT
🔍 [14:32:18] AI Auditor: Button injected successfully
🔍 [14:32:18] AI Auditor: Setting up blocking logic
```

### **👆 Нажатие кнопки анализа**
```
🔍 [14:32:25] AI Auditor: Analyze button clicked
🔍 [14:32:25] AI Auditor: 📝 getText from textarea {length: 150, preview: "Hello, my email is john@example.com and phone +7..."}
🔍 [14:32:25] AI Auditor: 🔍 Starting text analysis {textLength: 150}
```

### **🚨 Обнаружение рисков**
```
🔍 [14:32:25] AI Auditor: 🚨 Email PII detected {type: "pii", message: "Обнаружен email адрес", severity: "high"}
🔍 [14:32:25] AI Auditor: 🚨 Phone PII detected {type: "pii", message: "Обнаружен номер телефона", severity: "high"}
🔍 [14:32:25] AI Auditor: ✅ Analysis completed {totalFindings: 2, highRisk: 2, mediumRisk: 0}
```

### **📊 Отображение результатов**
```
🔍 [14:32:25] AI Auditor: 📊 Showing analysis results {findingsCount: 2, severities: ["high", "high"]}
🔍 [14:32:25] AI Auditor: 📤 Sending analysis to popup {type: "ANALYSIS_COMPLETED", url: "...", findings: [...]}
```

### **🚫 Блокировка (если включена)**
```
🔍 [14:32:30] AI Auditor: Checking for blocking, text length: 150
🔍 [14:32:30] AI Auditor: BLOCKING submission due to high-risk findings
🔍 [14:32:35] AI Auditor: User chose to override block
```

---

## 🔧 Отладка проблем

### **❌ Кнопка не появляется**
Ищите в логах:
```
❌ No input element found {availableElements: [...]}
❌ No send button found {selectors: [...]}
```

### **❌ Не считывается текст**
Ищите в логах:
```
❌ getText: No input element available
📝 getText from textarea {length: 0, preview: ""}
```

### **❌ Анализ не работает**
Ищите в логах:
```
❌ No adapter found
🔍 Starting text analysis {textLength: 0}
```

---

## 🎮 Расширенная отладка

### Включить дополнительные логи:
1. В Console введите:
```javascript
// Показать все найденные элементы
console.log('Input elements:', document.querySelectorAll('textarea, [contenteditable="true"]'));
console.log('Send buttons:', document.querySelectorAll('button'));

// Проверить текущий адаптер
console.log('Current adapter:', window.currentAdapter);
```

### Проверить настройки:
```javascript
chrome.storage.local.get(['settings'], (result) => {
  console.log('Stored settings:', result.settings);
});
```

---

## 🎯 Типичные проблемы и решения

| Проблема | Что искать в логах | Решение |
|----------|-------------------|---------|
| Кнопка не появляется | `No input/send button found` | Обновить селекторы для новой версии ChatGPT |
| Текст не считывается | `getText: No input element` | Проверить тип поля (textarea vs contenteditable) |
| Анализ показывает "пусто" | `textLength: 0` | Убедиться что текст введен перед анализом |
| Блокировка не работает | `blockOnHighRisk: false` | Включить в настройках popup |

---

**💡 Совет:** Оставьте DevTools открытыми при тестировании для отслеживания всего процесса в реальном времени!
