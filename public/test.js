addEventListener("load", () => {
  fetch("/api/test")
    .then(async (res) => {
      if (res.ok) {
        const json = await res.json();
        document.querySelector("#ip").textContent = json.ip;
        document.querySelector("#ua").textContent = json.ua;
      }
    });
});
