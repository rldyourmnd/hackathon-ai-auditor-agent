import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Curestry - AI Prompt Optimization',
  description: 'Analyze, validate, and optimize prompts for Large Language Models',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}