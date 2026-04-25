module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./**/templatetags/**/*.py"
  ],
  theme: {
    extend: {
      colors: {
        brown: {
          primary: "#6B4F3A",
          dark: "#3E2C23"
        },
        cream: "#F8F1E7",
        gold: {
          soft: "#D4A373"
        }
      },
      boxShadow: {
        soft: "0 12px 40px rgba(62, 44, 35, 0.12)"
      },
      borderRadius: {
        "2xl": "1.25rem"
      }
    }
  },
  plugins: []
}
