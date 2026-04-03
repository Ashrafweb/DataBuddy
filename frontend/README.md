# DataBuddy Frontend

This is a Next.js application for querying databases using natural language, powered by AI.

## Getting Started

First, install the dependencies:

```bash
yarn install
# or
npm install
```

Then, run the development server:

```bash
yarn dev
# or
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## Environment Variables

Create a `.env.local` file in the root of the frontend directory:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Available Scripts

- `yarn dev` - Runs the app in development mode
- `yarn build` - Builds the app for production
- `yarn start` - Runs the built app in production mode
- `yarn lint` - Runs the linter

## Tech Stack

- **Next.js 15** - React framework with App Router
- **React 19** - UI library
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **Axios** - HTTP client
- **Lucide React** - Icons
- **Sonner** - Toast notifications

## Project Structure

```
src/
├── app/
│   ├── layout.js      # Root layout with fonts and metadata
│   ├── page.js        # Home page (main application)
│   └── globals.css    # Global styles
├── components/
│   └── ui/            # shadcn/ui components
├── hooks/             # Custom React hooks
└── lib/               # Utility functions
```

## Migration from CRA

This project was migrated from Create React App with CRACO to Next.js 15 for:

- Better performance with Server Components
- Built-in optimizations (fonts, images, etc.)
- Improved developer experience
- Better SEO capabilities
- Modern React features

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
