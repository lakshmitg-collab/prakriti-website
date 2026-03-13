// -------------------------
// DOM ELEMENTS
// -------------------------
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const photoPreview = document.getElementById("photoPreview");
const captureBtn = document.getElementById("captureBtn");
const questionsDiv = document.getElementById("questions");
const resultCard = document.getElementById("resultCard");
const resultDiv = document.getElementById("result");
const submitBtn = document.querySelector(".submit-btn");

let stream = null;
let capturedBlob = null;
let answers = {};
let useFrontCamera = true;

// -------------------------
// DISABLE SUBMIT IF ALREADY SUBMITTED (SESSION ONLY)
// -------------------------
if (sessionStorage.getItem("prakriti_submitted")) {
  submitBtn.disabled = true;
  submitBtn.innerText = "Already Submitted";
  submitBtn.style.opacity = "0.6";
  submitBtn.style.cursor = "not-allowed";

  resultCard.style.display = "block";
  resultDiv.innerHTML = "✅ You have already submitted the data. Thank you!";
}

// -------------------------
// CAMERA FUNCTIONS
// -------------------------
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
  })
  .then(s => {
    stream = s;
    video.srcObject = s;
    video.classList.add("active");
    photoPreview.classList.remove("active");
    captureBtn.hidden = false;
  })
  .catch(() => alert("Camera access failed"));
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

// -------------------------
// QUESTIONS
// -------------------------
const sections = [
  {
    title: "Physical & Body Characteristics",
    qs: [
      ["Q1. How would you describe your overall body build and muscle development?", ["Thin, lean, low muscle mass", "Moderately built, proportionate muscles", "Broad, heavy, well-developed muscles"]],
      ["Q2. How would you describe your body frame or chest width?", ["Narrow / slim frame", "Medium frame", "Broad / wide frame"]],
      ["Q3. How would you describe your body proportions or height relative to others?", ["Appears too short or too tall compared to average", "Medium / proportionate", "Long or well-proportioned"]],
      ["Q4. What best describes your natural skin complexion or color?", ["Black / dark", "Dark brown", "Dusky / wheatish", "Light brown / fair"]],
      ["Q5. What best describes the condition of your nails?", ["Dry, rough, brittle, easily breaking", "Sharp, flexible, pink, lustrous", "Thick, oily, smooth, polished"]],
      ["Q6. How sensitive is your skin to environment, cosmetics, or weather?", ["Very sensitive, easily irritated", "Normal sensitivity", "Less sensitive / thick skin"]]
    ]
  },
  {
    title: "Digestion, Appetite & Metabolism",
    qs: [
      ["Q7. How would you describe your appetite?", ["Irregular or low appetite", "Moderate and steady appetite", "Strong appetite, frequent hunger"]],
      ["Q8. How would you describe your digestion after meals?", ["Weak digestion, bloating or gas", "Moderate digestion", "Strong digestion, fast metabolism"]],
      ["Q9. How would you describe your metabolism and weight change?", ["Slow metabolism, difficult to gain weight", "Moderate metabolism", "Fast metabolism, weight changes easily"]],
      ["Q10. How are your bowel movements usually?", ["Constipation, dry stools", "Loose stools, frequent", "Regular and well-formed"]]
    ]
  },
  {
    title: "Food Preferences",
    qs: [
      ["Q11. Which taste(s) do you naturally prefer? (Select more than one if applicable)", ["Sweet", "Sour", "Salty", "Bitter", "Pungent(Spicy)","Astringent(dry/rough taste)"]],
      ["Q12. What best describes your dietary habit?", ["Vegan","Vegetarian", "Omnivorous(vegetarian + nonveg)"]]
    ]
  },
  {
    title: "Climate & Hydration",
    qs: [
      ["Q13. Which climate do you feel most comfortable in?", ["Cold climate", "Moderate climate", "Warm climate"]],
      ["Q14. How much water do you usually consume daily?", ["Low intake", "Moderate intake", "High intake"]]
    ]
  },
  {
    title:"Sleep, Energy & Activity",
    qs: [
      ["Q15. How would you describe your sleep pattern?", ["Light, disturbed, short sleep", "Moderate, balanced sleep", "Deep, long, heavy sleep"]],
      ["Q16. How would you describe your physical activity level?", ["Mostly sedentary", "Moderately active", "Highly active"]],
      ["Q17. How would you describe your daily energy levels?", ["Variable energy, easily fatigued", "Intense energy, driven and focused", "Slow but steady energy"]]
    ]
  },
  {
    title:"Sleep, Energy & Activity",
    qs: [
      ["Q15. How would you describe your sleep pattern?", ["Light, disturbed, short sleep", "Moderate, balanced sleep", "Deep, long, heavy sleep"]],
      ["Q16. How would you describe your physical activity level?", ["Mostly sedentary", "Moderately active", "Highly active"]],
      ["Q17. How would you describe your daily energy levels?", ["Variable energy, easily fatigued", "Intense energy, driven and focused", "Slow but steady energy"]]
    ]
  },
  
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

// -------------------------
// SUBMIT
// -------------------------
function submitForm() {

  if (submitBtn.disabled) return;

  if (!capturedBlob) return alert("Please capture a photo first");
  if (Object.keys(answers).length === 0)
    return alert("Please answer at least one question");

  const name = document.getElementById("name").value.trim();
  const age = document.getElementById("age").value.trim();

  if (!name || !age) return alert("Please enter name and age");

  submitBtn.disabled = true;
  submitBtn.innerText = "Submitting...";
  submitBtn.style.opacity = "0.6";

  const fd = new FormData();
  fd.append("image", capturedBlob, "photo.png");
  fd.append("answers", JSON.stringify(answers));
  fd.append("name", name);
  fd.append("age", age);

  fetch("https://prakriti-website.onrender.com/submit", {
    method: "POST",
    body: fd
  })
  .then(res => {
    if (!res.ok) throw new Error("Server error");
    return res.json();
  })
  .then(() => {
    // 🔒 Mark as submitted for THIS SESSION ONLY
    sessionStorage.setItem("prakriti_submitted", "true");

    submitBtn.innerText = "Already Submitted";
    submitBtn.style.cursor = "not-allowed";

    resultCard.style.display = "block";
    resultDiv.innerHTML = "✅ Data submitted successfully. Thank you!";
  })
  .catch(() => {
    submitBtn.disabled = false;
    submitBtn.innerText = "Submit Data";
    alert("Submission failed. Please try again.");
  });
}
