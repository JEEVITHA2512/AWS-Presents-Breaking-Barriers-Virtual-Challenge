# Aurora Product Webpage

This is a React-based product webpage for Aurora, an AI-powered interview assistant robot. The site features a modern, responsive design with a sticky navigation bar, hero section, about, features roadmap, video showcase, and footer. The project is built with Vite and prepared for AWS Amplify and S3 integration.

## Features

- **Sticky Navigation Bar**: Always accessible at the top for smooth navigation.
- **Hero Section**: Eye-catching introduction to Aurora.
- **About Section**: Learn more about Aurora's mission and technology.
- **Features Roadmap**: Visually striking, animated stepper/roadmap layout showing Aurora's capabilities.
- **Video Showcase**: Demo video with animated title and floating effects.
- **Footer**: Contact and copyright information.
- **Responsive Design**: Works beautifully on all devices.
- **Smooth Scrolling**: Navigation links smoothly scroll to each section.
- **Modern CSS**: Uses standard CSS and inline styles (no Tailwind). Styled-components can be added if desired.
- **Ready for AWS**: Structure and codebase are ready for AWS Amplify and S3 integration.

## Getting Started

### Prerequisites

- Node.js (v16 or later recommended)
- npm (v8 or later)

### Installation

1. Clone the repository:

   ```sh
   git clone <your-repo-url>
   cd nephlele-app
   ```

2. Install dependencies:

   ```sh
   npm install
   ```

3. Start the development server:

   ```sh
   npm run dev
   ```

4. Open your browser and go to [http://localhost:5173](http://localhost:5173)

## Project Structure

```
src/
  assets/         # Images, video, and static assets
  components/     # Reusable React components
  pages/          # Page-level React components
  sections/       # Main sections (Hero, About, Features, Videos, Footer)
  App.jsx         # Main app component
  main.jsx        # Entry point
public/           # Static public files
```

## Customization

- Update content in `src/sections/` for each section.
- Add or replace images and videos in `src/assets/`.
- Adjust styles in `src/sections/*.jsx` or add to `Videos.css`, `Footer.css`, etc.

## Deployment

- The app is ready for deployment to AWS Amplify, S3, or any static hosting provider.
- To build for production:

  ```sh
  npm run build
  ```

  The output will be in the `dist/` folder.

## License

MIT

---

**Aurora** — The future of interview preparation, powered by AI.
