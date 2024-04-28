function notePost() {
  const msg = document.querySelector("#message");

  fetch("/api/litey/post", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: msg.value,
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
}

function noteDelete(id) {
  fetch(`/api/litey/get?id=${encodeURIComponent(id)}`)
    .then((res) => {
      if (res.ok) {
        res.json()
          .then((json) => {
            if (!confirm(`本当にこのメッセージを削除しますか？\n${json.content}`)) {
              return;
            }

            fetch("/api/litey/delete", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                id,
              }),
            })
              .then((res2) => {
                if (res2.ok) {
                  alert("削除に成功しました！");
                } else {
                  alert("削除に失敗しました。");
                }
              });
          });
      }
    })
}

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
  document.querySelectorAll("#attachments").forEach((attachments) => {
    const content = attachments.textContent;
    attachments.textContent = undefined;
    attachments.style["display"] = "block";

    (content.match(/https?:\/\/[^\s]+/g) ?? []).forEach((link) => {
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
  });
});

addEventListener("load", () => {
  document.querySelectorAll("#date").forEach((date) => {
    const dateStr = date.textContent;
    date.textContent = new Date(dateStr).toLocaleString();
  });
});
