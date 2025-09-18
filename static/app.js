
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const uploadLabel = document.getElementById("uploadLabel");
const genBtn = document.getElementById("genBtn");
const statusEl = document.getElementById("status");
const gallery = document.getElementById("gallery");
const styleSel = document.getElementById("style");
const promptInput = document.getElementById("prompt");

let uploadedFile = null;
let uploadedUrl = null;

fileInput.addEventListener("change", async (e) => {
  const f = e.target.files?.[0];
  if (!f) return;
  uploadedFile = f;
  preview.src = URL.createObjectURL(f);
  preview.style.display = "block";
  uploadLabel.innerText = f.name;

  // Upload to server so we can show it later (MVP doesn't use it for generation)
  const fd = new FormData();
  fd.append("image", f);
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const j = await res.json();
  if (j.ok) {
    uploadedUrl = j.url;
  } else {
    console.warn("Upload failed", j);
  }
});

async function loadGallery() {
  const res = await fetch("/api/images");
  const j = await res.json();
  gallery.innerHTML = "";
  for (const item of j.images) {
    const card = document.createElement("div");
    card.className = "card-img";
    const img = document.createElement("img");
    img.src = item.url;
    img.loading = "lazy";
    const meta = document.createElement("div");
    meta.className = "meta";
    const dt = new Date(item.mtime * 1000).toLocaleString();
    meta.innerHTML = `<span>${dt}</span><a href="${item.url}" download>다운로드</a>`;
    card.appendChild(img);
    card.appendChild(meta);
    gallery.appendChild(card);
  }
}

genBtn.addEventListener("click", async () => {
  const comp = document.querySelector('input[name="composition"]:checked').value;
  const style = styleSel.value;
  const fd = new FormData();
  fd.append("composition", comp);
  fd.append("style", style);
  fd.append("prompt", promptInput.value || "");
  if (uploadedFile) fd.append("image", uploadedFile);

  genBtn.disabled = true;
  statusEl.innerText = "이미지 생성 중... (약 10~30초)";
  try {
    const res = await fetch("/api/generate", { method: "POST", body: fd });
    const j = await res.json();
    if (!j.ok) throw new Error(j.error || "생성 실패");
    statusEl.innerText = "완료! 갤러리에 추가되었습니다.";
    await loadGallery();
  } catch (e) {
    statusEl.innerText = "오류: " + e.message;
  } finally {
    genBtn.disabled = false;
  }
});

// Initial load
loadGallery();
