# Curestry Landing Page - Implementation Guidelines

## Project Overview
**Goal**: Create a comprehensive landing page for Curestry AI prompt analysis platform
**Framework**: Next.js 15 with App Router, integrated with existing admin dashboard
**Design**: Dark theme with mint/teal accents, professional AI SaaS aesthetic

## Landing Page Structure

### 1. Page Architecture
```
app/
├── (marketing)/              # Public marketing pages (no auth)
│   ├── layout.tsx           # Marketing layout with public header/footer
│   ├── page.tsx             # Main landing page
│   ├── about/page.tsx       # About page
│   ├── pricing/page.tsx     # Pricing page
│   ├── contact/page.tsx     # Contact page
│   └── demo/page.tsx        # Live demo page
├── (dashboard)/             # Protected admin pages
│   └── [existing structure] # Current admin dashboard
└── components/
    ├── marketing/           # Landing page components
    │   ├── hero-section.tsx
    │   ├── demo-section.tsx
    │   ├── problems-section.tsx
    │   ├── how-it-works.tsx
    │   ├── features-grid.tsx
    │   ├── contact-form.tsx
    │   └── footer.tsx
    └── ui/                  # Shared UI components
```

### 2. Content Sections (Top to Bottom)

#### A) Announcement Bar
- **Content**: "NEW Trial Curestry week — Any type of Prompt"
- **CTA**: "Trial week" button
- **Behavior**: Closeable, persists until closed
- **Style**: Dark background with mint accent

#### B) Header Navigation
- **Logo**: Curestry (left)
- **Navigation**: Roadmap • Docs • Pricing • Team
- **Actions**: Sign In (ghost) + Try Now (primary)
- **Behavior**: Fixed on scroll

#### C) Hero Section
- **Badge**: "Created in 2 days on hackathon"
- **H1**: "Make your prompts reliable in minutes"
- **Subtitle**: "See risks, apply fixes and ship better prompts – instantly"
- **CTAs**: "Try now" (primary) + "Book a demo" (secondary)
- **Background**: Dark with subtle gradient

#### D) Product Demo Section
- **Title**: "Analyze your prompt live"
- **Subtitle**: "Instantly scan your prompt for weak spots in clarity, stability, and factual accuracy"
- **Visual**: Large interface mockup showing:
  - Overall Quality score
  - Metrics: Clarity (100), Completeness (50), Effectiveness (20)
  - Issues list with severity levels
  - "Improvement applied" indicator

#### E) Value Proposition
- **Badge**: "AI Gulag Platform"
- **Title**: "Curestry is a tool that helps you write stronger, more reliable prompts"
- **Subtitle**: "Power any product or sales process with the freshest, most trusted data"

#### F) Problems Section
- **Title**: "Problems that we can solve"
- **Grid**: 4 cards
  1. **Hallucinations** - AI fabricates facts/incorrect information
  2. **Instability** - Same prompt gives different responses
  3. **Conflicting instructions** - Mixed/unclear instructions lead to unpredictability
  4. **Inefficient iterations** - Manual prompt editing slows down process

#### G) How It Works
- **Title**: "How it works"
- **Steps**: 3 cards
  1. **Type your prompt** - Works in ChatGPT, Claude, Gemini. No additional tools required
  2. **Instant analysis** - Highlights risk spots, suggests targeted fixes with explanations
  3. **Fix & run** - Accept recommendations with 1 click or edit manually

#### H) Differentiation
- **Title**: "What makes us different"
- **Grid**: 6 features
  1. **Real-time analysis** - Facts, clarity, stability (not just grammar)
  2. **Actionable fixes** - Specific improvements, not just problem flags
  3. **Works everywhere** - Browser extension, no separate app needed
  4. **Beyond previews** - Explains why prompts break, not just output
  5. **Iterative improvement** - Fix → test → recheck cycle
  6. **Future-proof path** - Today improver, tomorrow full agent debugger

#### I) Features Grid
- **Title**: "Curestry features"
- **Grid**: 3x2 feature cards
  1. **LLM Guardrails** - Rules and validations
  2. **Retrieval checks** - RAG verification
  3. **Determinism tools** - Consistency/temperature/seed control
  4. **Team templates** - Shared prompt libraries
  5. **CI for prompts** - Regression testing
  6. **Analytics** - Quality dashboard and metrics

#### J) Contact Forms
- **Simple Contact Form**:
  - Name field (placeholder: "Timur")
  - Email field (placeholder: "gmail")
  - Message field (placeholder: "Words")
  - Submit button
- **Demo Request**: Large "Book a demo" button

#### K) Footer
- **Company**: About Us, Contact Us, Pricing
- **Products**: Curestry
- **Resources**: Documentation, Blog
- **Legal**: Terms, Privacy

## Technical Implementation

### 3. Route Groups Structure
```typescript
// app/(marketing)/layout.tsx
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-900">
      <MarketingHeader />
      <main>{children}</main>
      <MarketingFooter />
    </div>
  )
}

// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-900">
        <DashboardSidebar />
        <main className="pl-64">{children}</main>
      </div>
    </AuthGuard>
  )
}
```

### 4. Component Architecture

#### Reusable Components
```typescript
// components/marketing/section-wrapper.tsx
interface SectionWrapperProps {
  id?: string
  className?: string
  children: React.ReactNode
}

// components/marketing/feature-card.tsx
interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
  href?: string
}

// components/marketing/cta-button.tsx
interface CTAButtonProps {
  variant: 'primary' | 'secondary'
  size: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  href?: string
  onClick?: () => void
}
```

### 5. Styling Guidelines

#### Color Palette Implementation
```css
/* Extend existing theme */
:root {
  --color-mint: #10B981;
  --color-mint-light: #34D399;
  --color-mint-dark: #059669;

  /* Landing-specific colors */
  --color-hero-bg: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  --color-card-bg: rgba(30, 41, 59, 0.8);
  --color-card-border: rgba(51, 65, 85, 0.5);
}
```

#### Component Styles
```typescript
// Tailwind classes for common patterns
const styles = {
  section: "py-16 px-6 max-w-7xl mx-auto",
  sectionTitle: "text-3xl md:text-4xl font-bold text-slate-50 text-center mb-4",
  sectionSubtitle: "text-lg text-slate-400 text-center mb-12 max-w-3xl mx-auto",
  card: "bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 hover:border-emerald-500/50 transition-all duration-200",
  ctaPrimary: "bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-lg font-medium transition-all",
  ctaSecondary: "border border-slate-600 hover:border-slate-500 text-slate-300 px-6 py-3 rounded-lg transition-all"
}
```

### 6. API Integration Points

#### Contact Form Submission
```typescript
// POST /api/contact
interface ContactFormData {
  name: string
  email: string
  message: string
  source: 'landing' | 'demo'
}

// POST /api/demo-request
interface DemoRequestData {
  email: string
  company?: string
  useCase?: string
}
```

#### Analytics Tracking
```typescript
// Track user interactions
const trackEvent = (event: string, properties: Record<string, any>) => {
  // Integration with analytics service
}

// Key events to track
- 'landing_page_view'
- 'cta_click' (try_now, book_demo, contact)
- 'section_scroll' (demo, problems, features)
- 'form_submit' (contact, demo_request)
```

### 7. Performance Optimization

#### Image Optimization
- Use Next.js Image component for all images
- Optimize hero background and demo screenshots
- Lazy load images below the fold
- Use WebP format with fallbacks

#### Code Splitting
- Lazy load marketing components
- Separate bundle for landing vs dashboard
- Preload critical route chunks

#### SEO Optimization
```typescript
// app/(marketing)/page.tsx metadata
export const metadata: Metadata = {
  title: 'Curestry — Make your prompts reliable in minutes',
  description: 'Analyze prompts live, see risks, apply fixes, and ship better results instantly. Works with ChatGPT, Claude, Gemini.',
  keywords: ['AI prompts', 'prompt engineering', 'ChatGPT', 'Claude', 'prompt analysis'],
  openGraph: {
    title: 'Curestry — AI Prompt Analysis & Optimization',
    description: 'Make your prompts reliable in minutes',
    images: ['/og-image.jpg'],
  },
}
```

### 8. Animation & Interactions

#### Scroll Animations
```typescript
// Use Framer Motion for scroll-triggered animations
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 }
}

const staggerChildren = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
}
```

#### Micro-interactions
- Hover effects on cards and buttons
- Smooth scrolling to sections
- Loading states for forms
- Success/error feedback

### 9. Responsive Design

#### Breakpoints
- **Mobile**: 320px - 767px (1 column layouts)
- **Tablet**: 768px - 1023px (2 column grids)
- **Desktop**: 1024px+ (3+ column grids)

#### Mobile-First Approach
```typescript
// Responsive grid example
const gridClasses = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
const heroClasses = "text-center px-4 md:px-6 lg:px-8"
```

### 10. Content Management

#### Static Content
- All copy stored in TypeScript constants
- Easy to update and maintain
- Type-safe content structure

#### Dynamic Content (Future)
- CMS integration ready
- A/B testing capability
- Internationalization support

## Success Metrics

### Conversion Goals
1. **Primary**: Try Now button clicks → Extension installs
2. **Secondary**: Demo requests → Sales qualified leads
3. **Tertiary**: Contact form submissions → Support/feedback

### Technical Metrics
- Page load time < 2s
- Core Web Vitals scores > 90
- Mobile-friendly score 100%
- SEO score > 95%

### User Experience Metrics
- Bounce rate < 40%
- Average session duration > 2 minutes
- Scroll depth to features section > 60%
