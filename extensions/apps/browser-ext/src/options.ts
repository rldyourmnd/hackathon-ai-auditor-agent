import { loadSettings, saveSettings, SettingsSchema } from '@extensions/shared';

const modeEl = document.getElementById('mode') as HTMLSelectElement;
const baseUrlEl = document.getElementById('baseUrl') as HTMLInputElement;
const apiKeyEl = document.getElementById('apiKey') as HTMLInputElement;
const saveBtn = document.getElementById('save') as HTMLButtonElement;

(async function init() {
  const s = await loadSettings();
  modeEl.value = s.mode;
  baseUrlEl.value = s.baseUrl;
  apiKeyEl.value = s.apiKey;
})();

saveBtn.addEventListener('click', async () => {
  const parsed = SettingsSchema.safeParse({
    version: 1,
    mode: modeEl.value,
    baseUrl: baseUrlEl.value.trim(),
    apiKey: apiKeyEl.value.trim(),
    autoAnalyzeOnPaste: false,
    maxLength: 2000,
    flags: { enableMock: modeEl.value === 'mock' },
  });
  if (!parsed.success) {
    alert('Invalid settings');
    return;
  }
  await saveSettings(parsed.data);
  alert('Saved');
});


