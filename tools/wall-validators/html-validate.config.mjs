import { defineConfig } from "html-validate";

/** HTML structure. Same-origin scripts are not required to carry SRI. */
export default defineConfig({
  extends: ["html-validate:standard"],
  elements: ["html5"],
  rules: {
    "aria-label-misuse": "off",
  },
});
