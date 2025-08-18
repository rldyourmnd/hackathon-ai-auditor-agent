import { defineConfig } from 'vite';
import path from 'node:path';

const r = (p: string) => path.resolve(__dirname, p);
const repo = (p: string) => path.resolve(__dirname, '../../', p);

export default defineConfig({
  root: __dirname,
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        background: r('src/background.ts'),
        content: r('src/content.ts'),
        popup: r('public/popup.html'),
        options: r('public/options.html'),
      },
      output: {
        entryFileNames: 'src/[name].js',
        assetFileNames: (chunkInfo) => {
          if (/(popup|options)\.html$/.test(chunkInfo.name || '')) return '[name][extname]';
          return 'public/[name][extname]';
        },
      },
    },
  },
  resolve: {
    alias: {
      '@extensions/shared': repo('packages/shared/src'),
      '@extensions/messaging': repo('packages/messaging/src'),
      '@extensions/ui': repo('packages/ui/src'),
      '@extensions/core': repo('packages/core/src'),
      '@extensions/client-sdk': repo('packages/client-sdk/src'),
      '@extensions/adapters': repo('packages/adapters/src'),
    },
  },
});


