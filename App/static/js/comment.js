// toggle comment form show/hide
function toggleCommentForm(postId) {
    const form = document.getElementById(`comment-form-${postId}`);
    form.style.display = form.style.display === "none" ? "block" : "none";
}

// comment form handling
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".comment-form").forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();

            const postId = this.id.split("-")[2];
            const formData = new FormData(this);

            fetch(`/comment/${postId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken")
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // ✅ Append new comment
                    const list = document.getElementById(`comments-list-${postId}`);
                    if (list) {
                        list.insertAdjacentHTML("beforeend", `
                          <div class="comment-item">
                              <strong>${data.user}</strong>: ${data.text}
                              <small>just now</small>
                          </div>
                        `);
                    }

                    // ✅ Update comment count
                    document.getElementById(`comments-count-${postId}`).innerText = data.comments_count;

                    // ✅ Clear textarea
                    this.querySelector("textarea").value = "";

                    // ✅ Hide the form after submit
                    this.style.display = "none";
                }
            })
            .catch(err => console.error("Error:", err));
        });
    });
});



// after comment togle form close



document.addEventListener("click", function(e) {
  const btn = e.target.closest(".btn-see-comments");
  if (!btn) return;

  const postId = btn.dataset.post;
  const full = document.getElementById(`all-comments-${postId}`);
  if (!full) return;

  if (full.style.display === "none" || full.style.display === "") {
    full.style.display = "block";
    btn.textContent = "Hide comments";
    // optional: scroll to bottom of the comments list to show newest
    full.scrollTop = full.scrollHeight;
  } else {
    full.style.display = "none";
    btn.textContent = `View more comments (${full.querySelectorAll('.comment-item').length})`;
  }
});