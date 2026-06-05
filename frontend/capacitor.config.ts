import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "ai.landseeker.mobile",
  appName: "LandSeeker AI",
  webDir: "dist",
  server: {
    androidScheme: "https"
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1800,
      backgroundColor: "#0f766e",
      showSpinner: false
    },
    StatusBar: {
      style: "DARK",
      backgroundColor: "#ffffff"
    }
  }
};

export default config;
