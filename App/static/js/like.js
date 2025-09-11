(function(){
  // helper: read CSRF cookie
  function getCookie(name) {
    const v = `; ${document.cookie}`;
    const parts = v.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
  const csrftoken = getCookie('csrftoken');

  // one delegated handler for all like buttons
  document.addEventListener('click', async function(e){
    const btn = e.target.closest('.btn-like');
    if (!btn) return;

    e.preventDefault();

    const postId = btn.dataset.post;
    const url = btn.dataset.likeUrl || `/like/${postId}/`;

    // prevent concurrent clicks
    if (btn.dataset.pending === "true") return;
    btn.dataset.pending = "true";
    btn.disabled = true;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
      });

      if (!res.ok) {
        console.error('Like request failed', res.status, await res.text());
        return;
      }

      const data = await res.json();
      // update DOM
      btn.dataset.liked = data.liked ? "true" : "false";
      const countEl = document.getElementById(`likes-count-${postId}`);
      if (countEl) countEl.innerText = data.likes_count;

      btn.classList.toggle('liked', data.liked);
      btn.innerHTML = data.liked
        ? `👍 <span id="likes-count-${postId}">${data.likes_count}</span>`
        : `👍 <span id="likes-count-${postId}">${data.likes_count}</span>`;

    } catch (err) {
      console.error('Like failed', err);
    } finally {
      btn.dataset.pending = "false";
      btn.disabled = false;
    }
  });
})();