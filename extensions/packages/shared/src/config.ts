import { z } from 'zod';

export const FeatureFlagsSchema = z.object({
  enableMock: z.boolean().default(true),
  enableInlineHints: z.boolean().default(false),
});

export const SettingsSchemaV1 = z.object({
  version: z.literal(1),
  mode: z.enum(['mock', 'remote']).default('mock'),
  baseUrl: z.string().url().or(z.literal('')).default(''),
  apiKey: z.string().default(''),
  autoAnalyzeOnPaste: z.boolean().default(false),
  maxLength: z.number().int().positive().default(2000),
  flags: FeatureFlagsSchema.default({}),
});
export type SettingsV1 = z.infer<typeof SettingsSchemaV1>;

export type Settings = SettingsV1;
export const SettingsSchema = SettingsSchemaV1;

export const DEFAULT_SETTINGS: Settings = SettingsSchema.parse({ version: 1 });

export async function loadSettings(): Promise<Settings> {
  try {
    const raw = await chrome.storage.local.get('settings');
    if (!raw || !raw.settings) return DEFAULT_SETTINGS;
    return migrateSettings(raw.settings);
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function migrateSettings(data: unknown): Settings {
  // Only V1 currently
  const v1 = SettingsSchemaV1.safeParse(data);
  if (v1.success) return v1.data;
  return DEFAULT_SETTINGS;
}

export async function saveSettings(next: Settings): Promise<void> {
  await chrome.storage.local.set({ settings: next });
}


