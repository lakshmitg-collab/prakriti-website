const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const photoPreview = document.getElementById("photoPreview");
const captureBtn = document.getElementById("captureBtn");
const questionsDiv = document.getElementById("questions");
const downloadLink = document.getElementById("downloadLink");
const resultCard = document.getElementById("resultCard");
const resultDiv = document.getElementById("result");

let stream = null;
let capturedBlob = null;
let answers = {};
let useFrontCamera = true;

// ---------------- CAMERA ----------------
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
}

function startCamera() {
  stopCamera();
  navigator.mediaDevices.getUserMedia({
    video: { facingMode: useFrontCamera ? "user" : "environment" }
  }).then(s => {
    stream = s;
    video.srcObject = s;
    video.classList.add("active");
    photoPreview.classList.remove("active");
    captureBtn.hidden = false;
  }).catch(() => alert("Camera access failed"));
}

function switchCamera() {
  useFrontCamera = !useFrontCamera;
  startCamera();
}

function capture() {
  const ctx = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);

  canvas.toBlob(blob => {
    capturedBlob = blob;
    photoPreview.src = URL.createObjectURL(blob);
    photoPreview.classList.add("active");
    video.classList.remove("active");
  });

  stopCamera();
  captureBtn.hidden = true;
}

// ---------------- QUESTIONS ----------------
const sections = [
  {
    title: "Body Build & Weight",
    qs: [
      ["Q1. Body frame?", ["Thin", "Medium", "Heavy"]],
      ["Q2. Weight change?", ["Hard to gain", "Stable", "Easy gain"]]
    ]
  },
  {
    title: "Digestion",
    qs: [
      ["Q3. Appetite?", ["Low", "Strong", "Moderate"]],
      ["Q4. Digestion?", ["Irregular", "Fast", "Slow"]],
      ["Q5. After eating?", ["Bloated", "Energetic", "Sleepy"]],
      ["Q6. Bowel?", ["Dry", "Loose", "Heavy"]]
    ]
  }
];

let qid = 1;
sections.forEach(section => {
  let html = `<h3>${section.title}</h3>`;
  section.qs.forEach(q => {
    html += `<p><b>${q[0]}</b></p><div class="option-grid">`;
    q[1].forEach(opt => {
      html += `<div class="option-box"
        onclick="toggleOption(this,'${qid}','${opt}')">${opt}</div>`;
    });
    html += `</div>`;
    qid++;
  });
  questionsDiv.innerHTML += html;
});

function toggleOption(el, qid, val) {
  el.classList.toggle("selected");
  answers[qid] = answers[qid] || [];
  answers[qid].includes(val)
    ? answers[qid] = answers[qid].filter(v => v !== val)
    : answers[qid].push(val);
}

// ---------------- SUBMIT ----------------
function submitForm() {
  if (!capturedBlob) return alert("Capture photo first");

  const name = document.getElementById("name").value;
  const age = document.getElementById("age").value;

  const fd = new FormData();
  fd.append("image", capturedBlob, "photo.png");
  fd.append("answers", JSON.stringify(answers));
  fd.append("name", name);
  fd.append("age", age);

  fetch("https://prakriti-website.onrender.com/submit", {
    method: "POST",
    body: fd
  })
  .then(res => res.json())
  .then(data => {
    resultCard.style.display = "block";
    resultDiv.innerHTML = "✅ Data submitted successfully";
    if (data.pdf_id) {
      downloadLink.href =
        `https://prakriti-website.onrender.com/download/${data.pdf_id}`;
      downloadLink.innerText = "Download PDF";
    }
  })
  .catch(() => alert("Submission failed"));
}
