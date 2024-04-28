function createAttachment(link, proxyLink, mediaType) {
  if (mediaType.startsWith("image/")) {
    const img = document.createElement("img");
    img.src = proxyLink;
    img.loading = "lazy";
    img.decoding = "async";
    return img;
  } else if (mediaType.startsWith("audio/")) {
    const audio = document.createElement("audio");
    audio.src = proxyLink;
    audio.controls = true;
    audio.loop = true;
    audio.preload = "none";
    return audio;
  } else if (mediaType.startsWith("video/")) {
    const video = document.createElement("video");
    video.src = proxyLink;
    video.controls = true;
    video.loop = true;
    video.preload = "none";
    return video;
  } else {
    const a = document.createElement("a");
    a.href = link;
    a.textContent = link;
    return a;
  }
}

addEventListener("load", () => {
  const submit = document.querySelector("#message-submit")
  const message = document.querySelector("#message")

  submit.addEventListener("click", () => {
    fetch("/api/litey/post", {
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

  fetch("/api/litey/get")
    .then((res) => res.json())
    .then((json) => {
      json.forEach((item) => {
        const notes = document.querySelector("#notes");
        const note = document.createElement("div");
        const user = document.createElement("div");
        const content = document.createElement("div");
        const attachments = document.createElement("div");
        const date = document.createElement("code");
        const del = document.createElement("input");

        notes.insertAdjacentElement("afterbegin", note);
        note.insertAdjacentElement("beforeend", user);
        note.insertAdjacentElement("beforeend", content);
        note.insertAdjacentElement("beforeend", attachments);
        note.insertAdjacentElement("beforeend", date);
        note.insertAdjacentElement("beforeend", del);

        const uid = item.ip ? btoa(item.ip).slice(0, 11) : "-";
        user.textContent = uid;

        content.textContent = item.content;

        (item.content.match(/https?:\/\/[^\s]+/g) ?? [])
          .forEach((link) => {
            const proxyLink = `/api/litey/image-proxy?url=${encodeURIComponent(link)}`;

            fetch(proxyLink)
              .then((res) => {
                if (res.ok) {
                  const mediaType = res.headers.get("Content-Type");
                  const attachment = createAttachment(link, proxyLink, mediaType);
                  attachments.insertAdjacentElement("beforeend", attachment);
                }
              });
          });

        date.textContent = new Date(item.date).toLocaleString();

        del.type = "submit";
        del.value = "削除";

        del.addEventListener("click", () => {
          if (!confirm(`本当にこのメッセージを削除しますか？\n${item.content}`)) {
            return;
          }

          fetch("/api/litey/delete", {
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
