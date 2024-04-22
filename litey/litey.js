addEventListener("load", () => {
  const submit = document.querySelector("#message-submit")
  const message = document.querySelector("#message")

  submit.addEventListener("click", () => {
    fetch("/litey/post", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: message.value,
      }),
    })
      .then((res) => {
        if (res.ok) {
          message.value = "";
          alert("成功しました！");
        } else {
          alert("失敗しました。");
        }
      });
  });

  fetch("/litey/get")
    .then((res) => res.json())
    .then((json) => {
      json.forEach((item) => {
        const notes = document.querySelector("#notes");
        const note = document.createElement("div");
        const content = document.createElement("div");
        const date = document.createElement("code");
        const del = document.createElement("input");

        notes.insertAdjacentElement("afterbegin", note);
        note.insertAdjacentElement("beforeend", content);
        note.insertAdjacentElement("beforeend", date);
        note.insertAdjacentElement("beforeend", del);

        content.textContent = item.content;
        date.textContent = new Date(item.date).toLocaleString();

        del.type = "submit";
        del.value = "この投稿を削除";

        del.addEventListener("click", () => {
          fetch("/litey/delete", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              id: item.id,
            }),
          })
            .then((res) => {
              if (res.ok) {
                note.remove();
                alert("成功しました！");
              } else {
                alert("失敗しました。");
              }
            });
        });
      });
    });
});
