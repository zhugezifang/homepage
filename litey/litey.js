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
          alert("投稿に成功しました！");
        } else {
          alert("投稿に失敗しました。");
        }
      });
  });

  fetch("/litey/get")
    .then((res) => res.json())
    .then((json) => {
      json.forEach((item) => {
        const notes = document.querySelector("#notes");
        const note = document.createElement("div");
        const user = document.createElement("div");
        const content = document.createElement("div");
        const images = document.createElement("div");
        const date = document.createElement("code");
        const del = document.createElement("input");

        notes.insertAdjacentElement("afterbegin", note);
        note.insertAdjacentElement("beforeend", user);
        note.insertAdjacentElement("beforeend", content);
        note.insertAdjacentElement("beforeend", images);
        note.insertAdjacentElement("beforeend", date);
        note.insertAdjacentElement("beforeend", del);

        const uid = item.ip ? btoa(item.ip) : "-";
        user.id = "uid";
        user.textContent = uid;

        content.textContent = item.content;

        (item.content.match(/https?:\/\/[^\s]+/g) ?? [])
          .forEach((link) => {
            const img = document.createElement("img");
            img.src = `/image-proxy?url=${encodeURIComponent(link)}`;

            images.insertAdjacentElement("beforeend", img);

            img.addEventListener("error", () => {
              const a = document.createElement("a");
              a.href = link;
              a.textContent = link;

              img.remove();

              images.insertAdjacentElement("beforeend", a);
            });
          });

        date.textContent = new Date(item.date).toLocaleString();

        del.type = "submit";
        del.value = "削除";

        del.addEventListener("click", () => {
          if (!confirm(`本当にこのメッセージを削除しますか？\n${item.content}`)) {
            return;
          }

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
                alert("削除に成功しました！");
              } else {
                alert("削除に失敗しました。");
              }
            });
        });
      });
    });
});
