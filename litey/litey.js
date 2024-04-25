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
        const attrs = document.createElement("div");
        const date = document.createElement("code");
        const del = document.createElement("input");

        notes.insertAdjacentElement("afterbegin", note);
        note.insertAdjacentElement("beforeend", user);
        note.insertAdjacentElement("beforeend", content);
        note.insertAdjacentElement("beforeend", attrs);
        note.insertAdjacentElement("beforeend", date);
        note.insertAdjacentElement("beforeend", del);

        const uid = item.ip ? btoa(item.ip) : "-";
        user.id = "uid";
        user.textContent = uid;

        content.textContent = item.content;

        (item.content.match(/https?:\/\/[^\s]+/g) ?? [])
          .forEach((link) => {
            const proxyLink = `/image-proxy?url=${encodeURIComponent(link)}`;

            const v = document.createElement("video");
            v.src = proxyLink;
            v.controls = true;
            v.loop = true;
            attrs.insertAdjacentElement("beforeend", v);
            v.addEventListener("error", () => {              
              const i = document.createElement("img");
              i.src = proxyLink;
              v.remove();
              attrs.insertAdjacentElement("beforeend", i);
              i.addEventListener("error", () => {
                const a = document.createElement("a");
                a.href = link;
                a.textContent = link;
                i.remove();
                attrs.insertAdjacentElement("beforeend", a);
              })
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
