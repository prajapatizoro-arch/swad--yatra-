const $ = (s, c=document) => c.querySelector(s);
const escapeHTML = value => String(value || '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

function card(recipe) {
  return `<a class="recipe-card" href="/recipe/${encodeURIComponent(recipe.id)}" aria-label="Read ${escapeHTML(recipe.name)} recipe">
    <div class="card-image"><img src="${escapeHTML(recipe.image)}" alt="${escapeHTML(recipe.name)}" loading="lazy"><span class="region-pill">${escapeHTML(recipe.region)}</span></div>
    <div class="card-body"><div class="heritage">${escapeHTML(recipe.community)} heritage</div><div class="card-title">${escapeHTML(recipe.name)}</div><div class="card-locality"><span>⌖</span>${escapeHTML(recipe.locality)}</div></div>
  </a>`;
}

async function home() {
  const grid = $('#recipeGrid'); if (!grid) return;
  const [meta, initial] = await Promise.all([fetch('/api/meta').then(r=>r.json()), fetch('/api/recipes').then(r=>r.json())]);
  const regionSelect = $('#regionSelect'), communitySelect = $('#communitySelect');
  meta.regions.forEach(v => regionSelect.insertAdjacentHTML('beforeend', `<option value="${escapeHTML(v)}">${escapeHTML(v)}</option>`));
  meta.communities.forEach(v => communitySelect.insertAdjacentHTML('beforeend', `<option value="${escapeHTML(v)}">${escapeHTML(v)}</option>`));
  const urlFilters = new URLSearchParams(location.search);
  $('#searchInput').value = urlFilters.get('q') || '';
  regionSelect.value = urlFilters.get('region') || '';
  communitySelect.value = urlFilters.get('community') || '';
  let visible = 8, current = initial;
  if (urlFilters.toString()) {
    current = await fetch(`/api/recipes?${urlFilters}`).then(r=>r.json());
  }
  const paint = () => { grid.innerHTML = current.length ? current.slice(0, visible).map(card).join('') : '<div class="empty">No heritage recipes found here yet. Try another region or search term.</div>'; $('#loadMore').classList.toggle('hidden', visible >= current.length); };
  paint();
  $('#loadMore').onclick = () => { visible += 4; paint(); };
  $('#searchForm').onsubmit = async e => { e.preventDefault(); visible = 8; const params = new URLSearchParams({q:$('#searchInput').value, region:regionSelect.value, community:communitySelect.value}); current = await fetch(`/api/recipes?${params}`).then(r=>r.json()); paint(); document.querySelector('#discover').scrollIntoView({behavior:'smooth'}); };
}

async function recipePage() {
  const root = $('#recipePage'); if (!root) return;
  const id = location.pathname.split('/').filter(Boolean).pop();
  const response = await fetch(`/api/recipes/${encodeURIComponent(id)}`);
  if (!response.ok) { root.innerHTML = '<section class="section"><h1>That recipe has wandered off.</h1><p><a class="button" href="/">Return to the collection</a></p></section>'; return; }
  const r = await response.json(); document.title = `${r.name} · Swad Yatra`;
  const query = encodeURIComponent(r.videoQuery || `${r.name} recipe`);
  const video = r.videoUrl ? `<video controls src="${escapeHTML(r.videoUrl)}"></video>` : `<iframe class="video-frame" src="https://www.youtube-nocookie.com/embed?listType=search&list=${query}" title="${escapeHTML(r.name)} recipe video" allowfullscreen></iframe>`;
  root.innerHTML = `<a class="crumb" href="/">← Back to the journey</a><div class="recipe-hero"><div class="recipe-photo"><img src="${escapeHTML(r.image)}" alt="${escapeHTML(r.name)}"></div><div class="recipe-summary"><div class="heritage">${escapeHTML(r.region)} · ${escapeHTML(r.community)} heritage</div><h1>${escapeHTML(r.name)}</h1><p>${escapeHTML(r.about)}</p><div class="meta-row"><span>◷ ${escapeHTML(r.time)}</span><span>✦ ${escapeHTML(r.difficulty)}</span><span>⌖ ${escapeHTML(r.locality)}</span></div></div></div><div class="recipe-content"><main><section class="detail-block"><h2>The story</h2><p>${escapeHTML(r.about)}</p></section><section class="detail-block"><h2>Ingredients</h2><ul class="ingredients">${r.ingredients.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul></section><section class="detail-block"><h2>Method</h2><ol class="steps">${r.procedure.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ol></section><section class="detail-block"><h2>Goodness in the dish</h2><p>${escapeHTML(r.benefits)}</p><div class="nutrition"><div><b>${escapeHTML(r.calories)}</b><span>per serving</span></div><div><b>${escapeHTML(r.protein)}</b><span>protein</span></div></div></section></main><aside class="side"><div class="video-box"><h3>Watch it come alive</h3><p>Follow along with a video guide for this dish.</p>${video}</div><div class="side-card"><div class="heritage" style="color:#f2c76e">Taste it locally</div><h3>${escapeHTML(r.restaurant)}</h3><p>Recommended near ${escapeHTML(r.locality)}. Check opening hours before travelling.</p><a class="map-link" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.map || r.locality)}">⌖ Find on Google Maps</a></div></aside></div>`;
}

function submitPage() {
  const form = $('#submitForm'); if (!form) return;
  form.onsubmit = async event => { event.preventDefault(); const status = $('#formStatus'); status.textContent = 'Sending your story…'; status.style.color = 'var(--green)'; const response = await fetch('/api/submit', {method:'POST', body:new FormData(form)}); const data = await response.json(); if (response.ok) { form.reset(); status.textContent = 'Thank you — your recipe is now part of this session’s journey.'; } else { status.textContent = data.error || 'Could not submit the recipe. Please try again.'; status.style.color = '#b44029'; } };
}
home(); recipePage(); submitPage();
