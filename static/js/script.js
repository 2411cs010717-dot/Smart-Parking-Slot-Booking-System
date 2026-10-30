document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("imageInput");
  const fileName = document.getElementById("fileName");
  if (fileInput && fileName) {
    fileInput.addEventListener("change", () => {
      fileName.textContent = fileInput.files.length ? fileInput.files[0].name : "Click to browse files";
    });
  }
  const dateInput = document.getElementById("bookingDate");
  if (dateInput) {
    const today = new Date();
    const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    dateInput.min = localDate;
  }
  document.querySelectorAll(".flash").forEach((el) => {
    window.setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .4s"; }, 6000);
  });
});
