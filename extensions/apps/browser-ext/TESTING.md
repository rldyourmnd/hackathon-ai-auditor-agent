# 🧪 Тестирование AI Auditor - Пошаговая инструкция

## ⚡ Быстрый тест после обновления

### 1. **Обновите расширение**
- Откройте `chrome://extensions/`
- Найдите "AI Auditor"
- Нажмите кнопку **"Reload"** (обновить)

### 2. **Откройте ChatGPT**
- Перейдите на https://chatgpt.com
- Откройте **DevTools** (F12) → вкладка **Console**
- В фильтре введите: `AI Auditor`

### 3. **Проверьте логи инициализации**
Должны появиться логи:
```
🚀 AI Auditor content script loaded
🔍 [время] AI Auditor: 🚀 Initializing AI Auditor
🔍 [время] AI Auditor: 🌐 Starting site detection
🔍 [время] AI Auditor: ✅ Site detected: ChatGPT
🔍 [время] AI Auditor: 🔧 Initializing for ChatGPT
🔍 [время] AI Auditor: ✅ Button injected successfully
```

---

## 🎯 Тестовые сценарии

### **Тест 1: Проверка детектора слов**
1. Введите в ChatGPT: `проверка макарек тест`
2. Нажмите кнопку **"🔍 Analyze"**
3. **Ожидаемый результат:**
   ```
   🔍 [время] AI Auditor: 🧪 Test word detected
   AI Auditor - 1 findings
   ⚠️ Найдено тестовое слово "макарек"
   ```

### **Тест 2: Email детектор**
1. Введите: `Мой email: test@example.com`
2. Нажмите **"🔍 Analyze"**
3. **Ожидаемый результат:**
   ```
   🔍 [время] AI Auditor: 🧪 Test email detected
   🔍 [время] AI Auditor: 📧 Email check result {found: true}
   🔍 [время] AI Auditor: 🚨 Email PII detected
   AI Auditor - 2 findings
   ```

### **Тест 3: Телефон детектор**
1. Введите: `Позвони мне: +7 999 123 45 67`
2. Нажмите **"🔍 Analyze"**
3. **Ожидаемый результат:**
   ```
   🔍 [время] AI Auditor: 📱 Phone check result {found: true}
   🔍 [время] AI Auditor: 🚨 Phone PII detected
   ```

### **Тест 4: API ключ детектор**
1. Введите: `api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz123456789012"`
2. Нажмите **"🔍 Analyze"**
3. **Ожидаемый результат:**
   ```
   🔍 [время] AI Auditor: 🔐 OpenAI key pattern check {found: true}
   🔍 [время] AI Auditor: 🚨 Secret pattern detected
   ```

---

## 🔍 Отладка проблем

### **Проблема: Кнопка не появляется**
Ищите в логах:
```
❌ No input element found
❌ No send button found
```

**Решение:** Обновите страницу ChatGPT

### **Проблема: Анализ показывает 0 findings**
Ищите детальные логи:
```
🔍 Starting text analysis {textLength: X, textPreview: "..."}
📏 Checking length {length: X, threshold: 4000}
📧 Checking for email patterns
📧 Email check result {found: false}
🧪 Testing simple patterns
```

**Если логи не появляются:**
1. Убедитесь что обновили расширение
2. Перезагрузите страницу ChatGPT
3. Проверьте что кнопка "🔍 Analyze" видна

### **Проблема: Регулярные выражения не работают**
Проверьте в Console:
```javascript
// Тест email паттерна
const text = "test@example.com";
const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
console.log("Email test:", text.match(emailPattern));

// Тест телефона
const phoneText = "+7 999 123 45 67";
const phonePattern = /(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}/g;
console.log("Phone test:", phoneText.match(phonePattern));
```

---

## 📊 Ожидаемые логи для "ек макарек!"

При анализе текста "ек макарек!" должны появиться:

```
🔍 [время] AI Auditor: 👆 Analyze button clicked
🔍 [время] AI Auditor: 📝 getText from textarea {length: 11, preview: "ек макарек!"}
🔍 [время] AI Auditor: 🔍 Starting text analysis {textLength: 11, textPreview: "ек макарек!"}
🔍 [время] AI Auditor: 📏 Checking length {length: 11, threshold: 4000}
🔍 [время] AI Auditor: ✅ Length check passed
🔍 [время] AI Auditor: 📧 Checking for email patterns
🔍 [время] AI Auditor: 📧 Email check result {found: false}
🔍 [время] AI Auditor: ✅ No email found
🔍 [время] AI Auditor: 📱 Checking for phone patterns
🔍 [время] AI Auditor: 📱 Phone check result {found: false}
🔍 [время] AI Auditor: ✅ No phone found
🔍 [время] AI Auditor: 🔐 Checking for secret patterns
🔍 [время] AI Auditor: 🧪 Testing simple patterns
🔍 [время] AI Auditor: 🧪 Test word detected {type: "test-word", message: "Найдено тестовое слово 'макарек'"}
🔍 [время] AI Auditor: ✅ Analysis completed {totalFindings: 1, findingTypes: ["test-word"]}
```

**Если этих логов нет - значит проблема в функции analyzeText()!**
