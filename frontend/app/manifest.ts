import type { MetadataRoute } from "next";

const appName = "Turbo Bot";
const appColor = "#09090b";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: `${appName} — Admin Console`,
    short_name: appName,
    description: "Admin panel for the Turbo Discord music bot",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: appColor,
    theme_color: appColor,
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  };
}
