# AI Auditor Browser Extension

## 🚀 Как запускать в Cursor

### 1. Автоматическая сборка
В Cursor нажмите:
- `Ctrl+Shift+P` → "Tasks: Run Build Task" 
- Или `Ctrl+Shift+B`

### 2. Watch-режим (автоматическая пересборка)
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Watch Browser Extension"

### 3. Отладка в Chrome
- `F5` или `Ctrl+F5`
- Выберите "Launch Chrome with Extension"

---

## 🔧 Ручная сборка

```bash
# В терминале Cursor
cd extensions/apps/browser-ext
npx tsc -p .
```

---

## 📦 Установка в Chrome

1. Откройте `chrome://extensions/`
2. Включите "Developer mode"
3. "Load unpacked" → выберите папку `extensions/apps/browser-ext`
4. Готово! Идите на ChatGPT/Claude

---

## ✨ Функциональность

- 🔍 **Кнопка "Analyze"** — появляется на ChatGPT/Claude
- 🚨 **Детекция рисков** — email, телефоны, API ключи, длинные тексты
- ⚙️ **Настройки** — через popup расширения (кнопка в браузере)
- 🚫 **Блокировка отправки** — при включении строгого режима
- 📝 **История анализов** — последние 10 результатов

---

## 🐛 Отладка

- **Chrome DevTools** → F12 на веб-странице
- **Background Script** → `chrome://extensions/` → "background page"
- **Popup** → правый клик на иконке → "Inspect popup"

---

## 🔄 После изменений

1. Сохраните файлы в Cursor
2. Сборка (если не в watch-режиме)
3. Обновите расширение в `chrome://extensions/` (кнопка reload)
4. Перезагрузите веб-страницу
