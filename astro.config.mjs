import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://greenpipe.partners",
  base: "/docs/flux/0.1.0",
  outDir: ".runtime/site",
  integrations: [
    starlight({
      title: "Flux Docs",
      logo: { src: "./logo_hollow.png", alt: "Green Pipe Partners" },
      favicon: "/favicon.ico",
      customCss: ["./src/styles/greenpipe.css"],
      social: [{ icon: "github", label: "GitHub", href: "https://github.com/GreenPipePartners/Flux" }],
      sidebar: [
        {
          label: "Start Here",
          items: [
            { label: "Intro", slug: "" },
            { label: "Flux", slug: "flux" },
            { label: "Fluxy", slug: "fluxy" },
            { label: "Gateway functions", slug: "fluxy/gateway-functions" },
          ],
        },
        {
          label: "Examples",
          items: [
            { label: "NumPy tag analysis", slug: "fluxy/examples/numpy" },
          ],
        },
      ],
    }),
  ],
});
