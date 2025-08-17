# Frontend Development Guidelines - Curestry Platform

## Project Architecture Overview

### Technology Stack
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **State Management**: React Context + Custom hooks
- **Authentication**: NextAuth.js with custom providers
- **API Client**: Custom typed client with error handling
- **Charts**: Recharts for analytics visualization
- **Icons**: Lucide React
- **Fonts**: Geist Sans & Geist Mono

### Project Structure
```
frontend_public/
├── app/                          # Next.js App Router
│   ├── (marketing)/              # Public pages (no auth)
│   │   ├── layout.tsx            # Marketing layout
│   │   ├── page.tsx              # Landing page
│   │   ├── about/page.tsx        # About page
│   │   ├── pricing/page.tsx      # Pricing page
│   │   └── contact/page.tsx      # Contact page
│   ├── (dashboard)/              # Protected pages (auth required)
│   │   ├── layout.tsx            # Dashboard layout
│   │   ├── page.tsx              # Dashboard overview
│   │   ├── analytics/page.tsx    # Analytics page
│   │   ├── users/page.tsx        # User management
│   │   ├── sessions/page.tsx     # Session analytics
│   │   ├── settings/page.tsx     # Settings
│   │   └── usage/page.tsx        # Usage metrics
│   ├── api/                      # API routes
│   │   ├── auth/[...nextauth]/   # NextAuth.js routes
│   │   └── test-connection/      # API connection test
│   ├── globals.css               # Global styles
│   └── layout.tsx                # Root layout
├── components/                   # React components
│   ├── marketing/                # Landing page components
│   │   ├── hero-section.tsx
│   │   ├── demo-section.tsx
│   │   ├── problems-section.tsx
│   │   ├── how-it-works.tsx
│   │   ├── features-grid.tsx
│   │   ├── contact-form.tsx
│   │   └── footer.tsx
│   ├── analytics/                # Analytics components
│   │   ├── feature-usage-chart.tsx
│   │   ├── real-time-metrics.tsx
│   │   ├── session-duration-chart.tsx
│   │   ├── user-activity-heatmap.tsx
│   │   └── user-engagement-chart.tsx
│   ├── api/                      # API-related components
│   │   ├── api-status.tsx
│   │   └── error-boundary.tsx
│   ├── ui/                       # shadcn/ui components (47 components)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── [other ui components]
│   └── users/                    # User management components
│       ├── user-activity-timeline.tsx
│       ├── user-engagement-metrics.tsx
│       ├── user-session-analytics.tsx
│       └── user-table.tsx
├── lib/                          # Utility libraries
│   ├── api-client.ts             # Typed API client
│   ├── api-types.ts              # API TypeScript interfaces
│   ├── auth.ts                   # Authentication utilities
│   ├── utils.ts                  # General utilities
│   ├── curestry-ui-elements.md   # Brand guidelines
│   ├── landingguideline.md       # Landing page specs
│   └── frontendguideline.md      # This document
├── hooks/                        # Custom React hooks
│   ├── use-api.ts                # Generic API calls
│   ├── use-mobile.ts             # Mobile detection
│   └── use-toast.ts              # Toast notifications
├── styles/                       # Additional styles
│   └── globals.css               # Extended global styles
└── public/                       # Static assets
    ├── placeholder-logo.png
    ├── placeholder-user.jpg
    └── [other assets]
```

## Development Standards

### Code Style Guidelines

#### TypeScript Configuration
```typescript
// Strict mode enabled
{
  "strict": true,
  "noImplicitAny": true,
  "noImplicitReturns": true,
  "noUncheckedIndexedAccess": true
}

// Interface naming
interface UserData {          // Use PascalCase for interfaces
  id: string
  name: string
  email: string
}

// Component props
interface ButtonProps {      // Always type component props
  variant: 'primary' | 'secondary'
  size: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  onClick?: () => void
}
```

#### Component Structure
```typescript
// Standard component template
'use client'  // Only when needed (interactions, hooks)

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface ComponentProps {
  className?: string
  // ... other props
}

export function ComponentName({ className, ...props }: ComponentProps) {
  const [state, setState] = useState(initial)

  return (
    <div className={cn("default-classes", className)}>
      {/* Component content */}
    </div>
  )
}
```

#### File Naming Conventions
- **Components**: `kebab-case.tsx` (e.g., `user-table.tsx`)
- **Pages**: `page.tsx` in appropriate directory
- **Layouts**: `layout.tsx` in appropriate directory
- **Hooks**: `use-hook-name.ts` (e.g., `use-api.ts`)
- **Types**: `api-types.ts`, `user-types.ts`
- **Utils**: `kebab-case.ts` (e.g., `date-utils.ts`)

### Styling Guidelines

#### Tailwind CSS Best Practices
```typescript
// Use utility classes for common patterns
const styles = {
  // Layout
  container: "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8",
  section: "py-16 space-y-8",

  // Typography
  heading1: "text-4xl md:text-5xl font-bold tracking-tight",
  heading2: "text-3xl md:text-4xl font-semibold",
  body: "text-base text-slate-600 dark:text-slate-400",

  // Components
  card: "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6",
  button: "px-4 py-2 rounded-md font-medium transition-colors duration-200",

  // Interactive states
  hover: "hover:bg-slate-50 dark:hover:bg-slate-700",
  focus: "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2",
}

// Use cn() for conditional classes
import { cn } from '@/lib/utils'

<Button className={cn(
  "base-button-classes",
  variant === 'primary' && "primary-specific-classes",
  size === 'lg' && "large-size-classes",
  disabled && "disabled-classes"
)} />
```

#### CSS Custom Properties
```css
/* Use CSS variables for theme consistency */
:root {
  /* Colors */
  --color-primary: #10B981;
  --color-secondary: #6B7280;
  --color-background: #FFFFFF;
  --color-foreground: #111827;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Typography */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
}

/* Dark mode overrides */
[data-theme="dark"] {
  --color-background: #0F172A;
  --color-foreground: #F8FAFC;
}
```

### State Management Patterns

#### React Context for Global State
```typescript
// contexts/auth-context.tsx
interface AuthContextType {
  user: User | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Custom hooks for specific features
function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Implementation
  return { users, loading, error, refetch }
}
```

#### State Management Guidelines
1. **Local state**: `useState` for component-specific state
2. **Shared state**: React Context for auth, theme, global settings
3. **Server state**: Custom hooks with SWR-like patterns
4. **Form state**: React Hook Form for complex forms
5. **URL state**: Next.js router for navigation state

### API Integration Patterns

#### Typed API Client
```typescript
// lib/api-client.ts
interface ApiClientConfig {
  baseUrl: string
  timeout: number
  headers: Record<string, string>
}

class ApiClient {
  private config: ApiClientConfig

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    // Implementation with error handling
  }

  async post<T, D>(endpoint: string, data: D): Promise<ApiResponse<T>> {
    // Implementation with error handling
  }
}

// Usage in components
const { data, loading, error } = useApi<UserData>('/api/users')
```

#### Error Handling Strategy
```typescript
// lib/api-types.ts
interface ApiError {
  message: string
  code: string
  details?: Record<string, any>
}

interface ApiResponse<T> {
  data: T
  error: ApiError | null
  success: boolean
}

// Error boundary for API errors
function ApiErrorBoundary({ children, fallback }: Props) {
  return (
    <ErrorBoundary
      fallback={fallback}
      onError={(error) => {
        console.error('API Error:', error)
        // Send to monitoring service
      }}
    >
      {children}
    </ErrorBoundary>
  )
}
```

### Component Development Guidelines

#### Component Categories
1. **Page Components**: Top-level route components
2. **Layout Components**: Headers, sidebars, footers
3. **Feature Components**: Domain-specific functionality
4. **UI Components**: Reusable design system components
5. **Utility Components**: Error boundaries, providers

#### Component Best Practices
```typescript
// 1. Use composition over inheritance
function Card({ children, className, ...props }: CardProps) {
  return (
    <div className={cn("card-base", className)} {...props}>
      {children}
    </div>
  )
}

// 2. Implement proper prop forwarding
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    )
  }
)

// 3. Use proper TypeScript generics for flexible components
interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T>[]
  onRowClick?: (row: T) => void
}

function DataTable<T>({ data, columns, onRowClick }: DataTableProps<T>) {
  // Implementation
}
```

### Performance Optimization

#### Code Splitting
```typescript
// Lazy load components
const HeavyComponent = lazy(() => import('./heavy-component'))

// Use dynamic imports for conditional components
const DynamicChart = dynamic(() => import('./chart-component'), {
  loading: () => <ChartSkeleton />,
  ssr: false
})

// Route-level code splitting (automatic with App Router)
// app/dashboard/analytics/page.tsx automatically split
```

#### Image Optimization
```typescript
// Use Next.js Image component
import Image from 'next/image'

<Image
  src="/hero-image.jpg"
  alt="Curestry dashboard"
  width={1200}
  height={600}
  priority={true}  // For above-the-fold images
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
```

#### Bundle Optimization
```typescript
// Import only what you need
import { Button } from '@/components/ui/button'  // ✅ Good
import * as UI from '@/components/ui'            // ❌ Avoid

// Use tree-shaking friendly imports
import { format } from 'date-fns'               // ✅ Good
import { format } from 'date-fns/format'        // ✅ Even better
import * as dateFns from 'date-fns'             // ❌ Avoid
```

### Testing Guidelines

#### Component Testing
```typescript
// Use React Testing Library
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

#### API Testing
```typescript
// Mock API calls in tests
jest.mock('@/lib/api-client')

const mockApiClient = jest.mocked(apiClient)

beforeEach(() => {
  mockApiClient.get.mockResolvedValue({
    data: mockUserData,
    error: null,
    success: true
  })
})
```

### Accessibility Guidelines

#### Semantic HTML
```typescript
// Use proper semantic elements
<main>
  <section aria-labelledby="features-heading">
    <h2 id="features-heading">Features</h2>
    <ul role="list">
      <li>Feature 1</li>
      <li>Feature 2</li>
    </ul>
  </section>
</main>

// Proper form labeling
<div>
  <label htmlFor="email">Email Address</label>
  <input
    id="email"
    type="email"
    aria-describedby="email-help"
    aria-required="true"
  />
  <div id="email-help">We'll never share your email</div>
</div>
```

#### Keyboard Navigation
```typescript
// Implement proper focus management
function Modal({ isOpen, onClose }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.focus()
      // Trap focus within modal
    }
  }, [isOpen])

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose()
      }}
    >
      {/* Modal content */}
    </div>
  )
}
```

### Security Best Practices

#### Input Sanitization
```typescript
// Sanitize user input
import DOMPurify from 'isomorphic-dompurify'

function SafeHtml({ html }: { html: string }) {
  const cleanHtml = DOMPurify.sanitize(html)
  return <div dangerouslySetInnerHTML={{ __html: cleanHtml }} />
}

// Validate API responses
const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string().min(1)
})

function validateUser(data: unknown): User {
  return UserSchema.parse(data)
}
```

#### Environment Variables
```typescript
// Never expose secrets to client
// ✅ Server-only variables
DATABASE_URL=postgresql://...
API_SECRET_KEY=...

// ✅ Client-safe variables (NEXT_PUBLIC_ prefix)
NEXT_PUBLIC_API_URL=https://api.curestry.com
NEXT_PUBLIC_ANALYTICS_ID=GA_MEASUREMENT_ID

// Access in code
const apiUrl = process.env.NEXT_PUBLIC_API_URL
const secretKey = process.env.API_SECRET_KEY // Server-only
```

## Deployment Guidelines

### Build Optimization
```typescript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Optimize images
  images: {
    domains: ['example.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // Bundle analyzer
  bundleAnalyzer: {
    enabled: process.env.ANALYZE === 'true',
  },

  // Experimental features
  experimental: {
    // Enable when stable
  },
}
```

### Docker Configuration

```dockerfile
# Multi-stage build for optimal size
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY ../frontend_public/lib .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json
COPY --from=deps /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=${API_URL}
    depends_on:
      - backend
```
